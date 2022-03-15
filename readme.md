<div align="center">
<a href="https://gitlab.com/cossas/dgad/-/tree/master"><img src="dgad_logo.gif" height="300px"/>


![https://cossas-project.org](https://img.shields.io/badge/website-cossas--project.org-orange)
![Commits](https://gitlab.com/cossas/dgad/-/jobs/artifacts/master/raw/ci_badges/commits.svg)
![Pipeline status](https://gitlab.com/cossas/dgad/badges/master/pipeline.svg)
![Version](https://gitlab.com/cossas/dgad/-/jobs/artifacts/README/raw/version.svg?job=create_badge_svg)
![License: MPL2.0](https://gitlab.com/cossas/dgad/-/jobs/artifacts/README/raw/license.svg?job=create_badge_svg)
![Code-style](https://gitlab.com/cossas/dgad/-/jobs/artifacts/README/raw/code-style.svg?job=create_badge_svg)
</div></a>

<hr style="border:2px solid gray"> </hr>
<div align="center">
Hunt domains generated by Domain Generation Algorithms to identify malware traffic
</div>
<hr style="border:2px solid gray"> </hr>

_All COSSAS projects are hosted on [GitLab](https://gitlab.com/cossas/dgad/) with a push mirror to GitHub. For issues/contributions check [CONTRIBUTING.md](CONTRIBUTING.md)_ 

## What is it?
Domain generation algorithms (DGAs) are typically used by attackers to create fast changing domains for command & control channels.
The DGA detective is able to tell whether a domain is created by such an algorithm or not by using a variety of classification methods such as [TCN](https://github.com/philipperemy/keras-tcn) and LSTM. For example, a domain like `wikipedia.com` is not generated by an algorithm, whereas `ksadjfhlasdkjfsakjdf.com` is.

|  | Domain | Classification|
| ------ | ------ | --- |
|✅ | `wikipedia.org` | OK |
|❌ | `ksadjfhlasdkjfsakjdf.com` | DGA |

## Installation
To install the DGA Detective, we recommend using a virtual environment:

```bash
# recommended: use a virtual environment
python -m venv .venv
source .venv/bin/activate
pip install dgad
```

## How to use?
The DGA Detective can be used a Python package, through a command line interface or remotely through gRPC.

### Python package

```python
import dgad
etc.
```

### CLI
```bash
usage: dgad [-h] [--domains [DOMAIN [DOMAIN ...]]] [--model MODEL] [--csv CSV] [-q]

optional arguments:
  -h, --help            show this help message and exit
  --domains [DOMAIN [DOMAIN ...]]
                        space separated list of 1 or more domains you want DGA detective to classify
  --model MODEL         the hdf5 keras model file to pass to the classifier
  --csv CSV             csv file containing the domains to classify. This file must have a column 'domain'. The classification will be stored in the same file under a column
                        'classification'
  -q, --quiet           disables stdout
  ```

For example, if you want to classify one or several domains:
```bash
# classify one domain
$ dgad --domain wikipedia.org
          domain classification
0  wikipedia.org             ok

# classify several domains
$ dgad --domains wikipedia.org ksadjfhlasdkjfsakjdf.com
                     domain classification
0             wikipedia.org             ok
1  ksadjfhlasdkjfsakjdf.com            DGA
```

But you can also classify a large list of domains:

```bash
# classify from/to a csv file
$ dgad --csv your_csv_file.csv
```

### gRPC

**Server**

To initialize a DGA Detective server listening on port `50054`
```bash
# listens by default on port 50054
python dgad/grpc/classifier_server.py

# you can override default logging and port like this
LOG_LEVEL=info LISTENING_PORT=55666 python dgad/grpc/classifier_server.py
```

**Client**

A client example is provided at [dgad/grpc/classifier_client.py](dgad/grpc/classifier_client.py)

```bash
# you can override default destination host and port like this
GRPC_HOST=x.x.x.x GRPC_PORT=55666 python dgad/grpc/classifier_client.py
```

## Contributing

Contributions to the DGA Detective are highly appreciated and more than welcome. Please read [CONTRIBUTING.md](CONTRIBUTING.md) for more information about our contributions process. 

### Setup development environment
To create a development environment to make a contribution, follow these steps:

**Requirements**
* python >= 3.7
* [poetry](https://python-poetry.org)

**Setup**
```bash
# checkout this repository
git clone git@gitlab.com:cossas/dgad.git
cd dgad

# install project, poetry will spawn a new venv
poetry install

# (optional) install pre-commit hooks
pre-commit install
pre-commit install --hook-type commit-msg

# gRPC code generation
python -m grpc_tools.protoc -I dgad/grpc/protos --python_out=dgad/grpc --grpc_python_out=dgad/grpc dgad/grpc/protos/classification.proto
```

## About

DGA Detective is developed by TNO in the [SOCCRATES innovation project](https://soccrates.eu). SOCCRATES has received funding from the European Union’s Horizon 2020 Research and Innovation program under Grant Agreement No. 833481.
