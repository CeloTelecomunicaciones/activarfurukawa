from django.conf import settings
import telnetlib3
import time


def connect_to_telnet():
    try:
        host = settings.OLT_HOST
        port = settings.OLT_PORT
        # Create a Telnet object and connect to the specified host and port
        tn = telnetlib3.Telnet(host, port)
        print(f"Connected to {host} on port {port}")
        return tn, {
        "success": True,
        "message": "Conexión Telnet establecida."
        }
    except Exception as e:
        print(f"Failed to connect to {host} on port {port}: {e}")
        return {
            "success": False,
            "message": "Falla al conectar al OLT."
        }

def login(tn):
    try:
        username = settings.OLT_USERNAME
        password1 = settings.OLT_PASSWORD1

        # Read until the login prompt and send the username
        tn.read_until(b"login: ")
        tn.write(username.encode('ascii') + b"\n")
        
        # Read until the password prompt and send the password
        tn.read_until(b"Password: ")
        tn.write(password1.encode('ascii') + b"\n")
        print("Login successful")
        return {
            "success": True,
            "message": "Login exitoso."
        }
    except Exception as e:
        print(f"Login failed: {e}")
        return {
            "success": False,
            "message": "Falla al iniciar sesión."
        }

def enable_mode(tn):
    try:
        enable_password = settings.OLT_PASSWORD2
        # Send the 'enable' command
        tn.write(b"enable\n")
        
        # Read until the password prompt and send the enable password
        tn.read_until(b"Password: ")
        tn.write(enable_password.encode('ascii') + b"\n")
        
        # Optionally, read until a command prompt to confirm successful enable mode
        tn.read_until(b"#")  # Adjust this based on the actual prompt
        print("Entered enable mode successfully")
        return {
            "success": True,
            "message": "Modo de habilitación entrado exitosamente."
        }

    except Exception as e:
        print(f"Failed to enter enable mode: {e}")
        return {
            "success": False,
            "message": "Falla al entrar al modo de habilitación."
        }


#tengo que quedar con los ultimos 8 caracteres del mac para poder hacer el include en el comando show onu info | include 4f6ae908
#eliminar los dos puntos 
def format_onu_id(onu_id):
    onu_id = onu_id.replace(":", "")  # Remove colons
    return onu_id[-8:].lower()


def configure_onu(tn, onu_id):
    try:
        onu_id = format_onu_id(onu_id)
        # Enter configuration mode
        tn.write(b"conf t\n")
        response = tn.read_until(b"#", timeout=5).decode('ascii')
        print(f"Configuration Mode Response: {response}")
        
        print("Entered configuration mode")
        # Send the command to show ONU info and filter by ONU ID
        tn.write(f"show onu info | include {onu_id}\n".encode('ascii'))
        
        #leer la salida del comando para obtener la placa y puerto donde esta la onu
        try:
            response = tn.read_until(b"#", timeout=5).decode('ascii')
            print(f"ONU Info Response: {response}")
        except Exception as e:
            print(f"Failed to read ONU info response: {e}")
            return

        #cosas que importantes: X/Y (placa/puerto donde esta la onu)
        #Active
        #e identificador de la onu TPLG4f6ae908
        #Extract board/port from the response (this is a placeholder, adjust as needed) del segundo campo de la salida del comando show onu info | include 4f6ae908 
        #si es Activo pasar a sacar placa y puerto, si no es activo no hacer nada
        if "Active" not in response:
            print(f"ONU ID {onu_id} is not active. Skipping configuration.")
            return

        #ONU Info Response:  show onu info | include 4f6ae908
        #1/1 |   5 | Inactive | TPLG4f6ae908 |   5544m  | -          | oother_models 
        #2/3 |   8 |   Active | TPLG4f6ae908 |   5261m  | - 21.8 dBm | oother_models
        #respetar el ejemplo anterior
        #tomar de la ultima linea el primer campo que es la placa y puerto donde esta la onu, en este caso es 2/3
        board_port_info = None
        for line in response.splitlines():
            if onu_id in line and "Active" in line:
                board_port_info = line.split('|')[0].strip()
                print(f"Extracted Board/Port Info: {board_port_info}")
                break

        if not board_port_info:
            print(f"Could not find board/port information for ONU ID {onu_id}")
            return


        identificador_onu = None
        for line in response.splitlines():
            if onu_id in line and "Active" in line:
                identificador_onu = line.split('|')[3].strip()
                print(f"Extracted ONU Identifier: {identificador_onu}")
                break

        if not identificador_onu:
            print(f"Could not find ONU identifier for ONU ID {onu_id}")
            return
        
        # Enter GPON mode and configure the ONU
        tn.write(b"gpon\n")
        tn.write(f"gpon-olt {board_port_info}\n".encode('ascii'))
        tn.write(f"onu-profile {identificador_onu} oother_models\n".encode('ascii'))
        print(f"Configured ONU ID {identificador_onu} on board/port {board_port_info}")

        #volver a leer para ver si el oother_models es correcto
        tn.write(f"show onu info | include {onu_id}\n".encode('ascii'))
        time.sleep(5)  # Wait for the command to complete
        response = tn.read_until(b"#", timeout=5).decode('ascii')
        
        
        #si esta oother models en el ultimo elemento de la linea es poque se activo coorrectamente
        
        for line in response.splitlines():
            if onu_id in line and "Active" in line:
                if "oother_models" in line:
                    print(f"ONU ID {identificador_onu} configured successfully on board/port {board_port_info}. Response: {response}")
                    return {
                        "success": True,
                        "message": f"ONU con ID {identificador_onu} configurada exitosamente en placa/puerto {board_port_info}."
                    }
                else:
                    print(f"Failed to configure ONU ID {identificador_onu} on board/port {board_port_info}. Response: {response}")
                    return {
                        "success": False,
                        "message": f"Falla al configurar la ONU con ID {identificador_onu} en placa/puerto {board_port_info}."
                    }

        time.sleep(5)
        # Save the configuration
        tn.write(b"write memory\n")
        
        print("ONU configuration completed successfully")
        return {
            "success": True,
            "message": f"ONU con ID {identificador_onu} configurada exitosamente en placa/puerto {board_port_info}."
        }
    except Exception as e:
        print(f"Failed to configure ONU: {e}")
        return {
            "success": False,
            "message": "Falla al configurar la ONU."
        }


def close_connection(tn):
    try:
        tn.write(b"exit\n")
        tn.close()
        print("Telnet connection closed")
        return {
            "success": True,
            "message": "Telnet connection closed successfully."
        }
    except Exception as e:
        print(f"Failed to close Telnet connection: {e}")
        return {
            "success": False,
            "message": "Falla al cerrar la conexión Telnet."
        }


def habilitar(mac):
    try:
        tn, connection_result = connect_to_telnet()
        if not connection_result["success"]:
            return connection_result
        tn.timeout = settings.OLT_TIMEOUT
        time.sleep(2)
        
        login_result = login(tn)    
        if not login_result["success"]:
            return login_result
        tn.timeout = settings.OLT_TIMEOUT
        time.sleep(2)

        enable_result = enable_mode(tn)
        if not enable_result["success"]:
            return enable_result
        tn.timeout = settings.OLT_TIMEOUT
        time.sleep(2)


        configure_result = configure_onu(tn, mac)
        if configure_result is not None:
            return configure_result
        tn.timeout = settings.OLT_TIMEOUT
        time.sleep(2)

        cerrar_result = close_connection(tn)
        if not cerrar_result["success"]:
            return cerrar_result
        tn.timeout = settings.OLT_TIMEOUT
        time.sleep(2)

        return {
            "success": True,
            "message": f"ONU con MAC {mac} habilitada exitosamente."
        }
    except Exception as e:
        print(f"Error al habilitar la ONU: {e}")
        return {
            "success": False,
            "message": "Falla al habilitar la ONU."
        }