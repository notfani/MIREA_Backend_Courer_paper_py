FROM nginx:alpine

# Удаляем стандартную конфигурацию
RUN rm /etc/nginx/conf.d/default.conf

# Копируем нашу конфигурацию nginx
COPY nginx.conf /etc/nginx/nginx.conf


# Копируем страницу ошибки
COPY static/50x.html /usr/share/nginx/html/

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]

