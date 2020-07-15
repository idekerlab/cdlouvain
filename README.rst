===================================================
Community Detection Louvain
===================================================

.. image:: https://img.shields.io/pypi/v/cdlouvain.svg
        :target: https://pypi.python.org/pypi/cdlouvain

.. image:: https://img.shields.io/travis/idekerlab/cdlouvain.svg
        :target: https://travis-ci.org/idekerlab/cdlouvain

.. image:: https://readthedocs.org/projects/cdlouvain/badge/?version=latest
        :target: https://cdlouvain.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status

.. image:: https://requires.io/github/idekerlab/cdlouvain/requirements.svg?branch=master
        :target: https://requires.io/github/idekerlab/cdlouvain/requirements?branch=master
        :alt: Dependencies


This repository creates a CDAPS compatible community detection Docker image using Louvain
packaged from https://louvain-igraph.readthedocs.io/en/latest/index.html

* Work by iteratively optimizing modularity in each community, building hierarchy from the bottom layer (single nodes) up to the root layer.
* Input graph(s): Can be an edgelist directory for single graph or a list of edgelist directories for multiple graphs that have some share of nodes. If given multiple graphs, will automatically perform overlapping commnunity detection.
* Overlaping vs. deep community detection: cannot detect deep hierarchical clustering (hierarchy deeper than 2 layers; in other words, not just simple community assignment) and overlapping communities at the same time; in other words, 'overlap' and 'deep' cannot be both set to true.
* Graph weight: works on both weighted and unweighted graph; does not support negative edge weight

 * Param configmodel: the configuration model implemented. default: RB

 * RB: Implements Reichardt and Bornholdt’s Potts spin glass model with a configuration null model https://journals.aps.org/pre/abstract/10.1103/PhysRevE.74.016110
 * Param directed: true/false, whether a graph is directed or not (does not support half directed half undirected graph). default: false
 * Param overlap: true/false, whether or not allowing overlapping community detection. default: false Please see 'Input graph(s)' and 'overlapping vs. deep community detection' for conflicts
 * Param deep: true/false, detect hierarchy or not. default: false Please see 'Input graph(s)' and 'overlapping vs. deep community detection' for conflicts
 * Param interslice_weight: the weight on the new edge connecting same nodes shared by different graphs when multiple graphs is used. default: 0.1
 * Param resolution_parameter: resolution is an indicator of the number of communities. Since louvain build communites by iteratively merging child nodes, when the resolution parameter is high, louvain will perform this merging slowly while retaining a high number of relatively small commnities and stop merging and add the root node when number of community is still high; if the resolution parameter is low, louvain will quickly merge to a small number of relatively large communities and stop. (Short version: want more communities, use higher resolution_parameter and vice versa) default: 0.1

Dependencies
------------

* `Docker <https://www.docker.com/>`_
* `make <https://www.gnu.org/software/make/>`_ (to build)
* Python (to build)

Direct invocation
------------------

Version `0.2.0` can be directly pulled from dockerhub with this command:

.. code-block::

   docker pull coleslawndex/cdlouvain:0.2.0

Building
--------

.. code-block::

   git clone https://github.com/idekerlab/cdlouvain
   cd cdlouvain
   make dockerbuild

Run **make** command with no arguments to see other build/deploy options including creation of Docker image

.. code-block::

   make

Output:

.. code-block::

   clean                remove all build, test, coverage and Python artifacts
   clean-build          remove build artifacts
   clean-pyc            remove Python file artifacts
   clean-test           remove test and coverage artifacts
   lint                 check style with flake8
   test                 run tests quickly with the default Python
   test-all             run tests on every Python version with tox
   coverage             check code coverage quickly with the default Python
   docs                 generate Sphinx HTML documentation, including API docs
   servedocs            compile the docs watching for changes
   testrelease          package and upload a TEST release
   release              package and upload a release
   dist                 builds source and wheel package
   install              install the package to the active Python's site-packages
   dockerbuild          build docker image and store in local repository
   dockerpush           push image to dockerhub


Usage
-----

.. code-block::

   docker run -v coleslawndex/cdlouvain:0.2.0 -h

Credits
---------

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
