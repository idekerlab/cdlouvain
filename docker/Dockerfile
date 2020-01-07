FROM continuumio/miniconda3

RUN conda install -y -c conda-forge python-igraph
RUN conda install -y -c conda-forge igraph
RUN conda install -y -c conda-forge louvain

RUN mkdir /tmp/cdlouvain
COPY dist/*.whl /tmp/cdlouvain

RUN /opt/conda/bin/pip install /tmp/cdlouvain/cdlouvain*whl

RUN rm -rf /tmp/cdlouvain

ENTRYPOINT ["/opt/conda/bin/cdlouvaincmd.py"]
CMD ["--help"]
