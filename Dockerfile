FROM ubuntu
RUN apt-get update -y && apt-get -y upgrade
RUN apt-get install -y apache2
COPY . /var/www/html
CMD ["/usr/sbin/apache2ctl", "-D", "FOREGROUND"]
