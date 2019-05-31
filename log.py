from oslo_config import cfg
from oslo_log import log as logging

logging.register_options(cfg.CONF)
logging.set_defaults(default_log_levels="amqp=DEBUG,oslo.messaging=DEBUG")
logging.setup(cfg.CONF, __name__)
