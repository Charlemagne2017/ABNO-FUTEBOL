__author__ = 'alejandroaguado'

import sys
from ABNOParameters import ABNOParameters
from RestAPI import RestAPI
import thread

services = {}
params=ABNOParameters("ABNOParameters.xml")
RestAPI(params, services).begin()