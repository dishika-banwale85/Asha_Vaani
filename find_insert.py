with open(r'C:\Users\dishi\Downloads\Asha_Vaani-main\Asha_Vaani-main\backend.py', 'r', encoding='utf-8') as f:
    content = f.read()

idx = content.find('return {"status": "success"}\n    except Exception as e:')
if idx >= 0:
    print('Found at:', idx)
    print(repr(content[idx:idx+200]))
else:
    print('NOT FOUND')
    idx2 = content.find('return {"status": "success"}')
    if idx2 >= 0:
        print('Found alt at:', idx2)
        print(repr(content[idx2:idx2+300]))