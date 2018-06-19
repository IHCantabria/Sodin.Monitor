
from instagram.client import InstagramAPI
from instagram.bind import InstagramAPIError
from proveedores.configuracion import config_instagram


class Instagram(object):
    """Clase para trabajar con las fotos obtenidas de Instagram"""
    def __init__(self, log):
        self.log = log
        self.instagram_api = Instagram.autenticar_instagram(config_instagram.ACCESS_TOKEN,
                                                            config_instagram.CLIENT_SECRET)

    @staticmethod
    def autenticar_instagram(access_token, client_secret):
        try:
            return InstagramAPI(access_token=access_token, client_secret=client_secret)
        except InstagramAPIError as igerr:
            raise InstagramAPIError(igerr.status_code, igerr.error_type,
                                    u'Error autenticando cuenta de Instagram. {0}'.format(igerr.error_message))

    def buscar_posts(self, nombre_tag):
        numero_posts_peticion = 10
        max_tag_id = 0
        lista_posts, next_id = self.instagram_api.tag_recent_media(numero_posts_peticion,
                                                                   max_tag_id, nombre_tag)
        for post in lista_posts:
            print post.link
        return (lista_posts, next_id)
