###########################################################################################################################
# simulate job directory
export BASEDIR=$PWD
export RIVER_HOME=$PWD/work
export job_id="job_id"
mkdir -p $RIVER_HOME/jobs/job_id
cp $PWD/tests/params.json $RIVER_HOME/jobs/job_id/params.json
cd $RIVER_HOME/jobs/job_id
###########################################################################################################################
# Simulate flow of job script
echo "Checking requirements"
which micromamba || (echo "micromamba not found. Please install micromamba and try again." && exit 1)

# Install dependencies
if ! micromamba env list | grep -q 'river'; then
    micromamba create -y -n river python=3.12 conda-forge::singularity=3.8.6 bioconda::nextflow jq git -y
fi

# Activate environment
eval "$(micromamba shell hook --shell bash)"
micromamba activate river

# Setup networking
export PORT=$(python -c "import socket; s=socket.socket(); s.bind(('',0)); print(s.getsockname()[1]); s.close()")
echo $PORT > $RIVER_HOME/jobs/job_id/job.port
echo $(hostname) > $RIVER_HOME/jobs/job_id/job.host

# Load parameters and clone repository
while IFS== read -r key value; do
   export "$key=$value"
done < <(jq -r 'to_entries|map("\(.key)=\(.value|tostring)")|.[]' params.json)

git=$(git remote get-url origin 2>/dev/null)
repo_name=$(basename -s .git "$git")
owner=$(basename "$(dirname "$git")")
local_dir="$RIVER_HOME/tools/$owner/$repo_name/$tag"

if [[ "$git" == *"nf-"* ]]; then
    profiles="${profile:+singularity,$profile}"
    profiles="${profiles:-singularity}"
    nextflow run "$owner/$repo_name" \
        -r "$tag" \
        -c river.config \
        -profile "$profiles" \
        -process.executor slurm \
        -process.shell 'bash' \
        --outdir "s3://$bucket_name/$outdir/job_id" \
        -with-report "s3://$bucket_name/$outdir/job_id/report.html" \
        -resume
else
    bash $BASEDIR/river/main.sh
fi