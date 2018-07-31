
class MakeDataTest:
    def load_buy_list(self):
        f = open("/Users/B-dragon90/Desktop/Github/AjouStock/data/buy_list.txt", 'rt')
        buy_list = f.readlines()
        f.close()
        code_list = []
        for item in buy_list:
            split_row_data = item.split(';')
            code_list.append(split_row_data[1])
        return code_list
