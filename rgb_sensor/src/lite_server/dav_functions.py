
def delete(path):
    if os.path.isdir(path):
        os.rmdir(path)
    elif os.path.isfile(path):
        os.remove(path)

def create(path, content):
    file = open(fileName, 'w')
    file.write(data)
    file.close()
