
# custom interface for DGX-pyxis-slurm setup

import asyncio
import batchspawner
from traitlets import Integer, Unicode, Float, Dict, default, List

class PyxisSpawner(batchspawner.SlurmSpawner):

    # Pyxis does not support slurm --export option
    batch_script = Unicode(
"""#!/bin/bash
#SBATCH --output={{homedir}}/jupyter_dgx_%j.log
#SBATCH --job-name=jupyter-dgx
#SBATCH --chdir={{homedir}}
#SBATCH --get-user-env=L
{% if partition  %}#SBATCH --partition={{partition}}
{% endif %}{% if runtime    %}#SBATCH --time={{runtime}}
{% endif %}{% if memory     %}#SBATCH --mem={{memory}}
{% endif %}{% if gres       %}#SBATCH --gres={{gres}}
{% endif %}{% if ngpus      %}#SBATCH --gpus={{ngpus}}
{% endif %}{% if nprocs     %}#SBATCH --cpus-per-task={{nprocs}}
{% endif %}{% if reservation%}#SBATCH --reservation={{reservation}}
{% endif %}{% if containerimage%}#SBATCH --container-image '{{containerimage}}'
{% endif %}{% if containermounts%}#SBATCH --container-mounts {{containermounts}}
{% endif %}{% if options    %}#SBATCH {{options}}{% endif %}
set -euo pipefail
trap 'echo SIGTERM received' TERM
{{prologue}}
which jupyterhub-singleuser
{% if srun %}{{srun}} {% endif %}{{cmd}}
echo "jupyterhub-singleuser ended gracefully"
{{epilogue}}
""").tag(config=True)

    req_containerimage = Unicode(
            "").tag(config=True)

    req_containermounts = Unicode(
            "").tag(config=True)

    # override to not use sudo(exec_prefix) for checking status
    async def query_job_status(self):
        temp = self.exec_prefix
        self.exec_prefix = ""
        ret = await super(PyxisSpawner, self).query_job_status()
        self.exec_prefix = temp
        return ret

class PyxisFormSpawner(PyxisSpawner):

    container_options = List(Unicode())

    @default('container_options')
    def _default_container_options(self):
        opts = []
        for l in open("/etc/jupyterhub/container_whitelist.tsv"):
            v1, v2, v3 = l.rstrip().split("\t")
            txt = v1+"#"+v2+":"+v3
            opts.append(txt)
        return opts

    def _options_form_default(self):
        opts = []
        for l in self.container_options:
            opts.append('<option value={}>{}</option>'.format(l,l))
        return """
        <div class="form-group">
            <label for="cores">Cores:</label>
            <input type="number" name="cores" class="form-control slurm-var"
               min="1" max="32" value="1"></input>
        </div>
        <div class="form-group">
            <label for="mem">Memory (GB):</label>
            <input type="number" name="mem_gb" class="form-control slurm-var"
               min="2" max="120" value="2"></input>
        </div>
        <div class="form-group">
            <label for="container_image">Container Image:</label>
            <select name='container_image' class='form-control slurm-var'>
            {container_options}
            </select>
        </div>
        <div class='form-group'>
            <label for='n_gpus'>GPUs:</label>
            <select name='n_gpus' class='form-control slurm-var'>
            <option value='0'>no gpu</option>
            <option value='1'>1x A100 40GB</option>
            </select>
        </div>
        """.format(container_options="\n".join(opts))

    def sanitize_opt_int(self, options, key, default, vmin, vmax):
        if key in options:
            if options[key].isdigit():
                val = int(options[key])
                if val < vmin or val > vmax:
                    options[key] = default
            else:
                options[key] = default
        else:
            options[key] = default
        return options

    def sanitize_options(self, options):

        options = self.sanitize_opt_int(options, 'cores', '1', 1, 32)
        options = self.sanitize_opt_int(options, 'mem_gb', '2', 1, 120)
        options = self.sanitize_opt_int(options, 'n_gpus', '0', 0, 1)

        if 'container_image' not in options:
            options['container_image'] = self.container_options[0]
        elif options['container_image'] not in self.container_options:
            options['container_image'] = self.container_options[0]

        return options

    def set_batch_reqs(self, options):
        self.req_nprocs = options['cores']
        self.req_srun = ''
        self.req_runtime = '0'
        self.req_ngpus = options['n_gpus']
        self.req_memory = options['mem_gb']+'G'
        self.req_containerimage = options['container_image']
        self.req_containermounts = '/raid:/raid'
        self.batch_submit_cmd = 'sbatch --parsable --no-requeue'
        # batchspawner-singleuser must exist inside container
        # https://github.com/jupyterhub/batchspawner/issues/226
        self.req_prologue = 'pip install batchspawner==1.1'

    def options_from_form(self, formdata):
        options = {}
        for k in formdata.keys():
          options[k] = formdata[k][0]

        options = self.sanitize_options(options)
        self.set_batch_reqs(options)
        return options

