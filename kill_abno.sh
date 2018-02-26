#!/bin/bash

ps -ef | grep ABNOArch | awk '{print $2}' | sudo xargs kill -9
