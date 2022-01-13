#!/usr/bin/python
# -*- coding: UTF-8 -*-
import csv
import numpy as np
import requests
import time

value_write_file = "payment_value_satoshi_03.csv"

wrong = []

start_block = 672583  # timestamp 2021-03-01 00:02
end_block = 677167   # timestamp 2021-03-31 23:57



def getPaymentValue(start_block_height, end_block_height):
    global wrong

    with open(value_write_file, "w", newline='') as csvfile:
        csv_writer = csv.writer(csvfile)

        for i in range(start_block_height, end_block_height + 1):
            if i % 100 == 0:
                print('block：', i, time.asctime(time.localtime(time.time())))
            cur_block = 'https://blockchain.info/block-height/' + \
                str(i)+'?format=json'
            try:
                data = requests.get(cur_block).json()
            except (ValueError, requests.exceptions.ConnectionError, requests.exceptions.ChunkedEncodingError):
                print('wrong', i)
                wrong.append(i)
                time.sleep(10)
                continue
            for i_tx in range(1, len(data['blocks'][0]['tx'])):
                i_tx_amount = 0
                for j_out in range(0, len(data['blocks'][0]['tx'][i_tx]['out'])):
                    j_out_amount = data['blocks'][0]['tx'][i_tx]['out'][j_out]['value']
                    i_tx_amount = i_tx_amount + j_out_amount
                csv_writer.writerow([i_tx_amount])


def reGetPaymentValue(block_height):
    global wrong

    with open(value_write_file, "a", newline='') as csvfile:
        csv_writer = csv.writer(csvfile)

        cur_block = 'https://blockchain.info/block-height/' + \
            str(block_height)+'?format=json'
        try:
            data = requests.get(cur_block).json()
        except (ValueError, requests.exceptions.ConnectionError, requests.exceptions.ChunkedEncodingError):
            return

        for i_tx in range(1, len(data['blocks'][0]['tx'])):
            i_tx_amount = 0
            for j_out in range(0, len(data['blocks'][0]['tx'][i_tx]['out'])):
                j_out_amount = data['blocks'][0]['tx'][i_tx]['out'][j_out]['value']
                i_tx_amount = i_tx_amount + j_out_amount
            csv_writer.writerow([i_tx_amount])
        wrong.remove(block_height)


def main():
    print('start：', time.asctime(time.localtime(time.time())))
    getPaymentValue(start_block, end_block)
    while(len(wrong)):
        print('retry wrong：', time.asctime(time.localtime(time.time())))
        for i in wrong:
            reGetPaymentValue(i)
            print('retry wrong：', i, time.asctime(time.localtime(time.time())))

    print('done', time.asctime(time.localtime(time.time())))


main()
