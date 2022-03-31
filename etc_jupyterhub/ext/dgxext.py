
# interface customizada para iniciar notebook no slurm-pyxis

import asyncio
import batchspawner
import wrapspawner
from traitlets import Integer, Unicode, Float, Dict, default

class PyxisSpawner(batchspawner.SlurmSpawner):

    # Pyxis does not support --export
    batch_script = Unicode(
"""#!/bin/bash
#SBATCH --output={{homedir}}/jupyterhub_slurmspawner_%j.log
#SBATCH --job-name=spawner-jupyterhub
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

class PyxisFormSpawner(wrapspawner.WrapSpawner):
    def _options_form_default(self):
        container_options = []
        for l in open("/etc/jupyterhub/container_whitelist.tsv"):
            a, b, c = l.split("\t")
            txt = a+"#"+b+":"+c
            container_options.append('<option value={}>{}</option>'.format(txt,txt))
        return """
        <div class="form-group">
            <label for="cores">Cores . . . range: 1 ~ 32</label>
            <input type="number" name="cores" class="form-control slurm-var"
                placeholder="1" min="1" max="32"></input>
        </div>
        <div class="form-group">
            <label for="mem">Memory (GB) . . . range: 2 ~ 120</label>
            <input type="number" name="mem_gb" class="form-control slurm-var" 
               placeholder="2" min="2" max="120"></input>
        </div>
        <div class="form-group">
            <label for="container_image">Container Image</label>
            <select name='container_image' class='form-control slurm-var'>
            {container_options}
            </select>
        </div>
        <div class='form-group'>
            <label for='n_gpus'>GPUs</label>
            <select name='n_gpus' class='form-control slurm-var'>
            <option value='0'>no gpu</option>
            <option value='1'>1x A100 40GB</option>
            </select>
        </div>
        """.format(container_options="\n".join(container_options))

    def options_from_form(self, formdata):
        options = {}
        for k in formdata.keys():
          options[k] = formdata[k][0]
        return options

    def sanitize_options(self, options):
        if 'cores' in options:
            if options['cores'].isdigit():
                c = int(options['cores'])
                if c < 1 or c > 32:
                    options['cores'] = '1'
            else:
                options['cores'] = '1'
        else:
            options['cores'] = '1'
        if 'mem_gb' in options:
            if options['mem_gb'].isdigit():
                c = int(options['mem_gb'])
                if c < 1 or c > 120:
                    options['mem_gb'] = '2'
            else:
                options['mem_gb'] = '2'
        else:
            options['mem_gb'] = '2'
        if 'container_image' not in options:
            options['container_image'] = ''

        return options

    def set_child_options(self, options):
        options = self.sanitize_options(options)
        self.child_class = PyxisSpawner
        self.child_config = {
          'req_nprocs': options['cores'], 'req_srun': '',
          'req_runtime':'0', 'req_memory': options['mem_gb']+'G',
          'req_containerimage': options['container_image'],
          #'req_containermounts': '/raid:/raid',
          'batch_submit_cmd': 'sbatch --parsable --no-requeue',
          'req_prologue': 'pip install batchspawner'
        }

    # contruct the child spawner
    def construct_child(self):
        self.child_options = self.user_options
        self.set_child_options(self.child_options)
        super().construct_child()

    # load child state
    def load_child_class(self, state):
        try:
            self.child_options = state['options']
        except KeyError:
            self.child_options = {}
        self.set_child_options(self.child_options)

    def get_state(self):
        state = super().get_state()
        state['options'] = self.child_options
        return state

    def clear_state(self):
       super().clear_state()
       self.child_options = {}

