# pylint: disable-all

import logging
import sys
from importlib import resources
from typing import Any, Set

import click
import pandas as pd

import dgad.label_encoders
import dgad.models
from dgad.api import DGADClient, DGADServer  # type: ignore
from dgad.prediction import Detective, Model, pretty_print
from dgad.utils import load_labels, setup_logging

def dgad_server_thread():
    print("starting DGADServer")
    detective = Detective()
    server = DGADServer(detective=detective, port=4714, max_workers=10)
    server.bootstrap()

def validate_families_number(ctx: Any, param: Any, value: int) -> int:
    allowed = [52, 81]
    if value not in allowed:
        raise click.BadParameter(f"must be one of {allowed}")
    else:
        return value


def validate_file_format(ctx: Any, param: Any, value: str) -> str:
    allowed = ["csv", "jsonl", "txt"]
    if value not in allowed:
        raise click.BadParameter(f"must be one of {allowed}")
    else:
        return value


def input_domains_from_cli_filepath_or_buf(
    input_filepath_or_buf: Any, format: str, domains_column: str
) -> Set[str]:
    df = pd.DataFrame()
    if format == "csv":
        df = pd.read_csv(input_filepath_or_buf, index_col=False)
    elif format == "jsonl":
        df = pd.read_json(input_filepath_or_buf, lines=True)
    elif format == "txt":
        df = pd.read_csv(input_filepath_or_buf, names=[domains_column])
    if not df.empty:
        try:
            domains_set = set(df[domains_column].tolist())
        except KeyError:
            logging.critical(
                "you must have a {domains_column} column in your csv/jsonl file"
            )
            sys.exit(-1)
    return domains_set


def load_multi_class_model(n_families: int) -> Model:
    with resources.path(
        dgad.models, f"tcn_family_{n_families}_classes.h5"
    ) as model_path:
        with resources.path(
            dgad.label_encoders, f"encoder_{n_families}_classes.npy"
        ) as labels_path:
            model_multi = Model(filepath=model_path, labels=load_labels(labels_path))
    return model_multi


def analyse_domains_remotely(dgad_client: DGADClient, domains: Set[str]) -> None:
    responses = [dgad_client.requests(domain) for domain in domains]
    pretty_print(domains=responses)


@click.group()
def cli() -> None:
    """
    DGA Detective can predict if a domain name has been generated by a Domain Generation Algorithm
    """


@cli.command()
@click.option(
    "-d", "--domain", type=str, multiple=True, help="the domain(s) you want to check"
)
@click.option(
    "-f",
    "--input-filepath-or-buf",
    type=click.File("rb"),
    required=False,
    help="file containing the domains to check, can be piped through stdin from another command. When using this, you must specify a format with either --csv or --jsonl",
)
# TODO: what if I want to pass a url to a file in object storage?
# TODO: what if I want to pass a regex to handle multiple files?
@click.option(
    "-fmt", "--format", type=str, default="csv", callback=validate_file_format
)
@click.option(
    "-dc",
    "--domains_column",
    type=str,
    default="domain",
    help="the name of the column that contains the domains in your file",
)
@click.option(
    "-n",
    "--families-number",
    type=int,
    default=81,
    help="dgad comes with two trained models for family classification. They have been trained with examples from 52 and 81 families, respectively. This option allows you to choose the model by specifying the number of families in the model (thus this can be either 52 or 81)",
    callback=validate_families_number,
)
@click.option(
    "-r",
    "--remote-analysis",
    is_flag=True,
    default=False,
    help="send domains to remote DGAD server for analysis (instead of performing it locally)",
)
@click.option(
    "-h",
    "--remote-host",
    default="localhost",
    type=str,
    help="remote DGA Detective hostname/ip",
)
@click.option(
    "-p",
    "--remote-port",
    type=int,
    default=4714,
    help="remote DGA Detective port",
)
def client(
    domain: str,
    input_filepath_or_buf: Any,
    format: str,
    domains_column: str,
    families_number: int,
    remote_analysis: bool,
    remote_host: str,
    remote_port: int,
) -> None:
    """
    classify domains from cli args or csv/jsonl files
    """
    domains_set: Set[str] = set()
    # 1. input
    if domain:
        domains_set = set(domain)
    elif input_filepath_or_buf and format:
        domains_set = input_domains_from_cli_filepath_or_buf(
            input_filepath_or_buf, format, domains_column
        )
    # 2. classification
    if domains_set:
        if remote_analysis:
            dgad_client = DGADClient(host=remote_host, port=remote_port)
            analyse_domains_remotely(
                dgad_client=dgad_client,
                domains=domains_set,
            )
        else:
            # 2a. load a specific family model
            if families_number:
                multi_class_model = load_multi_class_model(n_families=families_number)
                detective = Detective(model_multi=multi_class_model)
            else:  # 2b or use defaults
                detective = Detective()
            # 3. run
            domains, _ = detective.prepare_domains(raw_domains=domains_set)
            detective.investigate(domains)
            # 4. output
            pretty_print(domains)


@click.option(
    "-v",
    "--verbosity",
    type=str,
    default="WARNING",
    help="sets log level, uses python logging module so you can pass strings like DEBUG, CRITICAL...",
)
@click.option(
    "-p",
    "--port",
    type=int,
    default=4714,
    help="DGAD grpc api will listen at this port",
)
@click.option(
    "-n",
    "--families-number",
    type=int,
    default=81,
    help="dgad comes with two trained models for family classification. They have been trained with examples from 52 and 81 families, respectively. This option allows you to choose the model by specifying the number of families in the model (thus this can be either 52 or 81)",
    callback=validate_families_number,
)
@click.option(
    "-w",
    "--max-workers",
    type=int,
    default=10,
    help="maximum amount of threads the grpc thread can spawn to handle incoming requests",
)
@cli.command()
def server(verbosity: str, port: int, families_number: int, max_workers: int) -> None:
    """
    deploy a DGA Detective server
    """
    setup_logging(level=verbosity)
    if families_number:
        multi_class_model = load_multi_class_model(n_families=families_number)
        detective = Detective(model_multi=multi_class_model)
    else:
        detective = Detective()
    server = DGADServer(detective=detective, port=port, max_workers=max_workers)
    server.bootstrap()

@click.option(
    "-p",
    "--port",
    type=int,
    default=8000,
    help="DGAD REST API Server will listen at this port",
)
@cli.command()
def ws(port: int) -> None:
    """
    WS listener
    """
    from dgad.web import app
    import threading
    threading.Thread(daemon=True, target=dgad_server_thread).start()
    app.run(debug=False, host='0.0.0.0', port=port)

if __name__ == "__main__":
    cli()

