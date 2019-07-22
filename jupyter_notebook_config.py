# Configuration file for ipython-notebook.
c = get_config()

# default notebook
c.NotebookApp.default_url='/notebooks/index.md'

# Only run ipynb and md as a notebook
c.ContentsManager.notebook_extensions = "ipynb,md"
