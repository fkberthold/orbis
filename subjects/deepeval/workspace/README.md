# The DeepEval workspace

Your DeepEval tests run from this folder, because this is where `deepeval`
is installed. It's a uv project pinned to `deepeval==4.3.2`. Install it once
with `uv sync`, which took about a second on a warm uv cache here.

Put your tests under `mine/`, one file per item, named after it, such as
`mine/test_01_order_status.py`. The file name has to start with `test_` or
pytest won't collect it.

Each item's app is a Python module in its own folder, so it has to be on
`PYTHONPATH` for your test to import it. From this folder, after `source
env.sh` (which turns DeepEval's telemetry off):

    PYTHONPATH=../items/01-order-status/app uv run deepeval test run mine/test_01_order_status.py

Each item's page shows the same command for that item, and how to grade it.
The gate stages its runs under `runs/`, which is ignored.
