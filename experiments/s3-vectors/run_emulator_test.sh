#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"
image=learning-s3-vectors-emulator:1.0.533
port=${S3V_EMULATOR_PORT:-9297}

runtime=$(docker info --format '{{.ServerVersion}} {{json .SecurityOptions}}')
major=${runtime%%.*}
if [[ ! "$major" =~ ^[0-9]+$ ]] || (( major < 28 )) || [[ "$runtime" == *name=rootless* || "$runtime" == *name=userns* ]]; then
    echo "Use a local Docker Engine 28+ with rootful Docker and no user namespace remapping." >&2
    exit 1
fi

docker build -t "$image" - < Dockerfile.emulator

state=$(mktemp -d)
container=
cleanup() {
    local status=$?
    if [[ -n "$container" ]] && ! docker stop "$container" >/dev/null; then
        status=1
    fi
    rm -rf -- "$state"
    exit "$status"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

container=$(docker run --detach --rm --memory=2g --memory-swap=2g \
    --user "$(id -u):$(id -g)" --env HOME=/emulator \
    --publish "127.0.0.1:$port:$port" --volume "$state:/emulator" \
    "$image" --port "$port" --telemetry off)
emulator_dir="$state/.aws/emulator/$port"

for ((attempt = 1; attempt <= 30; attempt++)); do
    if curl --noproxy '*' --silent --fail --max-time 1 --cacert "$emulator_dir/ca.pem" \
        "https://127.0.0.1:$port/__admin/health" >/dev/null; then
        S3V_EMULATOR_DIR="$emulator_dir" S3V_EMULATOR_PORT="$port" \
            uv run --locked python -m unittest -v test_emulator
        exit 0
    fi
    sleep 1
done

docker logs --tail 15 "$container" >&2
echo "AWS Emulator did not become ready" >&2
exit 1
