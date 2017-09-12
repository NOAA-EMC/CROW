import trace
import os

import crow.config
import crow.config.eval_tools
import crow.config.template
import crow.config.tasks
import yaml

trace_ignore = [ crow.config.eval_tools, crow.config.template, 
                 crow.config.tasks, yaml ]
