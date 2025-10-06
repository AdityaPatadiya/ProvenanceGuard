import logging


class LogConfigure():
    def __init__(self):
        self.log_configure_name = ""

    def setup_logging(self, log_file, logger):
        """Set up logging to file"""
        self.logger = logger
        self.logger.setLevel(logging.INFO)

        print(self.logger)
        fh = logging.FileHandler(log_file)
        fh.setLevel(logging.INFO)

        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)

        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)

        self.logger.addHandler(fh)
        self.logger.addHandler(ch)


        if self.logger.name == 'LogisticsAgent':
            self.log_configure_name = 'Logistic Agent'
        elif self.logger.name == 'SupplyChainAgent':
            self.log_configure_name = 'Supply Chain Agent'
        elif self.logger.name == 'BlockchainRecorder':
            self.log_configure_name = 'Blockchain recorder'
        else:
            self.log_configure_name = '{There is some error for the "log_configure_name"}'

        self.logger.info(f"{self.log_configure_name} initialized")
