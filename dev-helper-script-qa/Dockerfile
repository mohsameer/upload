FROM python:3.9.6

COPY requirements.txt /root/requirements.txt
COPY oidc_anchor_app_register.py /oidc_anchor_app_register.py


RUN pip install -r /root/requirements.txt \
    && chmod a+x /oidc_anchor_app_register.py
   

CMD ["/usr/bin/tail", "-f", "/dev/null"]
