import requests
import datetime
from os import path

def timeStamped(fname, fmt='%Y-%m-%d-%H-%M-%S-{fname}'):
        import datetime
        
        return datetime.datetime.now().strftime(fmt).format(fname=fname)
    
    
def get_image(image_url):
    """
    Get image based on url.
    :return: Image name if everything OK, False otherwise
    """
    image_name = timeStamped(path.split(image_url)[1])
    try:
        image = requests.get(image_url)
    except OSError:  
        return False
    if image.status_code == 200:  #
        
        base_dir = path.join(project_path, 'data\\raw\\img')
        
        with open(path.join(base_dir, image_name), 'wb') as f:
            f.write(image.content)
        return image_name


project_path = 'E:\\work\\ML\\volcano\\'
src_url = 'http://volcano.febras.net/archive/latest_Klyu2.jpg'

name = get_image(src_url)
if not(name): print('Сервер не доступен') 
else: print('Файл создан: ', name)

