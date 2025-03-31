from configparser import ConfigParser
"""
Created on Thu Feb 27 12:50:00 2025

@author: mgoddard
"""

class Settings():
    '''
    Subclass of ConfigParser, with an added feature of adding a section only if does not exist

    '''
    def __init__(self):
        self.settings = ConfigParser()
        self.settings.read('settings.ini')

    def add_section(self, section):
        self.settings.add_section(section)

    def add_section_safely(self, section):
        section_does_not_exists = True
        for sec in self.settings:
            if sec == section:
                section_does_not_exists = False
        if section_does_not_exists:
            self.settings.add_section(section)
        else:
            pass

    def set(self, section, option, value):
        self.settings.set(section, option, value)

    def get(self, section, option):
        return self.settings.get(section, option)

    def getint(self, section, option):
        return self.settings.getint(section, option)
    
    def getfloat(self, section, option):
        return self.settings.getfloat(section, option)

    def getboolean(self, section, option):
        return self.settings.getboolean(section, option)

    def save(self):
        try:
            with open('settings.ini', 'w') as settingsfile:
                self.settings.write(settingsfile)
        except:
            pass
        
# class Settings(ConfigParser):
#     '''
#     Subclass of ConfigParser, with an added feature of adding a section only if does not exist

#     '''
#     def __init__(self):
#         self.read('settings.ini')

#     def add_section(self, section):
#         self.add_section(section)

#     def add_section_safely(self, section):
#         section_does_not_exists = True
#         for sec in self:
#             if sec == section:
#                 section_does_not_exists = False
#         if section_does_not_exists:
#             self.add_section(section)
#         else:
#             pass

#     def set(self, section, option, value):
#         self.set(section, option, value)

#     def get(self, section, option):
#         return self.get(section, option)

#     def getint(self, section, option):
#         return self.getint(section, option)
    
#     def getfloat(self, section, option):
#         return self.getfloat(section, option)

#     def getboolean(self, section, option):
#         return self.getboolean(section, option)

#     def save(self):
#         try:
#             with open('settings.ini', 'w') as settingsfile:
#                 self.write(settingsfile)
#         except:
#             pass