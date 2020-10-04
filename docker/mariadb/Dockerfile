FROM mariadb:latest

# RUN sed -i 's/#general_log_file/general_log_file/g' /etc/mysql/my.cnf
# RUN sed -i 's/#general_log /general_log /g' /etc/mysql/my.cnf
RUN sed -i 's/max_heap_table_size[ \t]*= 32M/max_heap_table_size\t= 10G/g' /etc/mysql/my.cnf
RUN sed -i 's/tmp_table_size[ \t]*= 32M/tmp_table_size\t= 10G/g' /etc/mysql/my.cnf
RUN sed -i 's/wait_timeout[\t ]*= 600/wait_timeout\t= 28800/g' /etc/mysql/my.cnf
RUN echo 'interactive_timeout\t= 28800' >> /etc/mysql/my.cnf

