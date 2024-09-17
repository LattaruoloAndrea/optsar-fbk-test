FROM ubuntu:18.04
COPY main.py .
COPY requirements.txt .
COPY environment.yml .
COPY config.ini .
COPY libs /libs
#RUN add-apt-repository -y ppa:jblgf0/python
RUN apt-get update
RUN dpkg --configure -a && apt install -y python3.6-distutils
RUN  apt-get update \
  && apt-get install -y wget \
  && rm -rf /var/lib/apt/lists/*
RUN wget https://bootstrap.pypa.io/pip/3.6/get-pip.py
RUN python3.6 get-pip.py
RUN python3.6 -m pip install --upgrade pip
RUN python3.6 -m pip install wheel
RUN python3.6 -m pip install -r requirements.txt
#RUN add-apt-repository ppa:ubuntugis/ppa
#RUN apt-get update
#RUN apt-get install -y binutils libproj-dev gdal-bin
#RUN apt-get install gdal-bin
#RUN apt-get install libgdal-dev
#RUN export CPLUS_INCLUDE_PATH=/usr/include/gdal
#RUN export C_INCLUDE_PATH=/usr/include/gdal
#RUN python -m pip install GDAL

#RUN mkdir -p /opt/conda 


#RUN wget https://repo.anaconda.com/miniconda/Miniconda3-py38_4.12.0-Linux-x86_64.sh -O /opt/conda/miniconda.sh \ && bash /opt/conda/miniconda.sh -b -p /opt/miniconda 
# Install your environment.yaml deps into base env 
# Uncomment once you are ready to start productionizing the image 
# COPY environment.yaml /tmp 
# RUN . /opt/miniconda/bin/activate && conda env update --name base --file /tmp/environment.yaml

#RUN conda install gdal
ENTRYPOINT [ "python3.6","main.py" ]