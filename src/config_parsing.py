from configparser import ConfigParser

def readConfig(filename):
    conf = ConfigParser() 
    conf.read(filename)

    # convert to dictionary
    conf_dict = {}
    for section_name in conf.sections():
        options = dict(conf.items(section_name))
        conf_dict[section_name] = options
    return conf_dict

