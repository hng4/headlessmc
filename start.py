#!/usr/bin/env python

import getpass
import time
import sys
import re
import json
import requests

from minecraft import authentication
from minecraft.exceptions import YggdrasilError
from minecraft.networking.connection import Connection
from minecraft.networking.packets import Packet, clientbound, serverbound

def main():
#    r = requests.get("https://status.mojang.com/check")
#    e = r.json()
    check = ['minecraft.net',
             'session.minecraft.net',
             'account.mojang.com',
             'authserver.mojang.com',
             'sessionserver.mojang.com',
             'api.mojang.com',
             'textures.minecraft.net',
             'mojang.com']
    cotos = {"green": "up",
             "yellow": "partially down",
             "red": "down"
    }

#    for x in e:
#        for f in check:
#            try:
#                print(f +": "+ cotos[x[f]])
#            except:
#                None

    opt_username = "yourEmail"
    opt_password = "yourPass"
    opt_offline = False # broken for now
    opt_user = "H_Bot"
    opt_host = "192.168.0.101"
    opt_port = 25565
    opt_dp = True # Dump packets
    opt_du = False # Dump unknown packets (DONT)
    opt_dispose = ["0x26"] # [:4]
#    cur_x = 0
#    cur_y = 63
#    cur_z = 0
    auth_token = authentication.AuthenticationToken()
    try:
        auth_token.authenticate(opt_username, opt_password)
    except YggdrasilError as e:
        print(e)
        sys.exit()
    print("Logged in as %s..." % auth_token.username)
    connection = Connection(
        opt_host, opt_port, auth_token=auth_token)

    if opt_dp:
        def print_incoming(packet):
            if type(packet) is Packet:
                # This is a direct instance of the base Packet type, meaning
                # that it is a packet of unknown type, so we do not print it
                # unless explicitly requested by the user.
                if opt_du:
                    print('--> [unknown packet] %s' % packet, file=sys.stderr)
#            else:
#                print(packet[:4])
#                print('--> %s' % packet, file=sys.stderr)

        def print_outgoing(packet):
            print('<-- %s' % packet, file=sys.stderr)

#        connection.register_packet_listener(
#            print_incoming, Packet, early=True)
#        connection.register_packet_listener(
#            print_outgoing, Packet, outgoing=True)

    def handle_join_game(join_game_packet):
        print('Connected.')

    connection.register_packet_listener(
        handle_join_game, clientbound.play.JoinGamePacket)

    def send_chat(text):
        packet = serverbound.play.ChatPacket()
        packet.message = text
        connection.write_packet(packet)

    def print_chat(chat_packet):
        ef = json.loads(chat_packet.json_data)
        sys_send = chat_packet.field_string('position')
        print(chat_packet.json_data)
        try:
            print("[x] "+ef['translate']+" event from "+sys_send)
            event = 1
        except:
            event = 0
        if event == 1:
            if(ef['translate'][:5] == "death"):
                try:
                    died_w = ef['with'][0]['insertion']
                except:
                    died_w = "noone"
                try:
                    died_bc = ef['with'][1]['insertion']
                except:
                    died_bc = "noone"
                print("[x] "+str(died_w)+" died because of "+str(died_bc)+" ("+str(ef['translate'])+")")
                if died_w == opt_user:
                    print("[x] We died, respawning.")
                    packet = serverbound.play.ClientStatusPacket()
                    packet.action_id = serverbound.play.ClientStatusPacket.RESPAWN
                    connection.write_packet(packet)

    def get_coords():
        f = open("last_coords.txt", "r")
        e = f.read()
        f.close()
        return e

    def store_coords(x, y, z):
        f = open("last_coords.txt", "w")
        f.write(str(x)+","+str(y)+","+str(z))
        f.close()

    def handle_movement(packet):
        cur_x = packet.x
        cur_y = packet.y
        cur_z = packet.z
        f = open("last_coords.txt", "w")
        f.write(str(cur_x)+","+str(cur_y)+","+str(cur_z))
        f.close()
        print("[x] Moved to "+str(round(packet.x))+", "+str(round(packet.y))+", "+str(round(packet.z)))

    connection.register_packet_listener(handle_movement,clientbound.play.PlayerPositionAndLookPacket)
    connection.register_packet_listener(print_chat, clientbound.play.ChatMessagePacket)
    connection.connect()

    pck = serverbound.play.PositionAndLookPacket()
    pck.yaw = 0
    pck.pitch = 0
    pck.on_ground = True

    while True:
        try:
            text = input()
            if text == "/respawn":
                print("respawning...")
                packet = serverbound.play.ClientStatusPacket()
                packet.action_id = serverbound.play.ClientStatusPacket.RESPAWN
                connection.write_packet(packet)
            elif text.split(" ")[0] == "/mz":
                print("[/] Moving "+str(text.split(" ")[3])+" (on the Z axis) for "+str(text.split(" ")[1])+" times with a "+str(text.split(" ")[2])+" delay.")
                ttm = (float(text.split(" ")[3]) * int(text.split(" ")[1]))
                stm = (int(ttm) * float(text.split(" ")[2]))
                cd_first = get_coords()
                for x_time in range(0, int(text.split(" ")[1])):
                    nc = get_coords().split(",")
                    pck.x = float(nc[0])
                    pck.feet_y = float(nc[1])
                    pck.z = (float(nc[2])+float(text.split(" ")[3]))
                    print("[x] Currently at "+str(nc[0])+", "+str(nc[1])+", "+str(nc[2]))
                    print("[/] Moving to "+str(pck.x)+", "+str(pck.feet_y)+", "+str(pck.z))
                    connection.write_packet(pck)
                    store_coords(pck.x, pck.feet_y, pck.z)
                    if(int(text.split(" ")[1]) > 0):
                        time.sleep(float(text.split(" ")[2]))
                print("[x] Finished moving "+str(ttm)+" Z changes in "+str(stm)+" seconds")
            elif text.split(" ")[0] == "/mx":
                print("[/] Moving "+str(text.split(" ")[3])+" (on the X axis) for "+str(text.split(" ")[1])+" times with a "+str(text.split(" ")[2])+" delay.")
                ttm = (float(text.split(" ")[3]) * int(text.split(" ")[1]))
                stm = (int(ttm) * float(text.split(" ")[2]))
                for x_time in range(0, int(text.split(" ")[1])):
                    nc = get_coords().split(",")
                    pck.x = (float(nc[0])+float(text.split(" ")[3]))
                    pck.feet_y = float(nc[1])
                    pck.z = (float(nc[2]))
                    print("[x] Currently at "+str(nc[0])+", "+str(nc[1])+", "+str(nc[2]))
                    print("[/] Moving to "+str(pck.x)+", "+str(pck.feet_y)+", "+str(pck.z))
                    connection.write_packet(pck)
                    store_coords(pck.x, pck.feet_y, pck.z)
                    if(int(text.split(" ")[1]) > 0):
                        time.sleep(float(text.split(" ")[2]))
                print("[x] Finished moving "+str(ttm)+" X changes in "+str(stm)+" seconds")
            elif text.split(" ")[0] == "/move":
                nc = get_coords().split(",")
                pck.x = float(text.split(" ")[1])
                pck.feet_y = float(text.split(" ")[2])
                pck.z = float(text.split(" ")[3])
                print("[x] Currently at "+str(nc[0])+", "+str(nc[1])+", "+str(nc[2]))
                print("[/] Moving to "+str(pck.x)+", "+str(pck.feet_y)+", "+str(pck.z))
                connection.write_packet(pck)

            else:
                packet = serverbound.play.ChatPacket()
                packet.message = text
                connection.write_packet(packet)
        except KeyboardInterrupt:
            print("Bye!")
            sys.exit()

if __name__ == "__main__":
    main()
