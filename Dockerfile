FROM debian:buster-slim

#Setup a generic user
RUN useradd -ms /bin/bash bot_user
USER root

#Copy our app to a local folder
COPY . /home/bot_user/app
WORKDIR /home/bot_user/app

#Update debian and install pip
RUN apt-get update -y && apt-get install apt-utils -y
RUN apt-get install python3 python3-pip git -y

#Update sub-modules
RUN cd DDRGenie && git submodule init && git submodule update

#Install required dependencies
RUN pip3 install pillow
RUN pip3 install -r Requirements.txt

#Install sub-module dependencies
RUN cd DDRGenie && pip3 install -r Requirements.txt
RUN touch DDR_GENIE_ON

#Set user folder permissions
RUN chown -R bot_user:bot_user /home/bot_user

#Switch to bot_user
USER bot_user
RUN ls -l ~/app

#Run bot
ENTRYPOINT ["python3", "DDRBot.py"]
