import os
from SCons.Script import Import

listaVariabiliStr = [
    "AWS_IOT_ENDPOINT",
]

listaVariabiliRaw = [
    "AWS_IOT_PORT",
]

def read_cert(certs_dir, filename):
    path = os.path.join(certs_dir, filename)
    if os.path.exists(path):
        with open(path, "r") as f:
            return f.read().strip()
    return "NOT_FOUND"

def sync(project_dir=None):
    """
    Genera delle variabili globali di tipo DEFINE basandosi sul file 
    .env della cartella superiore e include i certificati AWS
    """

    if not project_dir:
        try:
            project_dir = os.path.dirname(os.path.abspath(__file__))
        except NameError:
            project_dir = os.getcwd()

    env_path = os.path.join(project_dir, "..", ".env")
    certs_dir = os.path.join(project_dir, "..", "certs")
    secrets_path = os.path.join(project_dir, "lib", "utils", "secrets.h")

    if not os.path.exists(env_path):
        print(f"--- ERRORE: .env non trovato in {env_path} ---")
        return

    defines = []
    
    try:
        # Scrittura variabili
        with open(env_path, "r") as f:
            for line in f:
                line = line.strip()
                
                if not line or line.startswith("#"):
                    continue
                
                if "=" in line:
                    key, value = line.split("=", 1)
                    key, value = key.strip(), value.strip()
                    
                    if key in listaVariabiliRaw:
                        defines.append(f'#define {key} {value}')

                    if key in listaVariabiliStr:
                        defines.append(f'#define {key} "{value}"')

        # Lettura certificati
        ca = read_cert(certs_dir, "rootCA.pem")
        crt = read_cert(certs_dir, "device.crt")
        key_content = read_cert(certs_dir, "private.key")

        with open(secrets_path, "w", encoding="utf-8") as f:
            f.write("// --- FILE GENERATO AUTOMATICAMENTE ---\n\n")
            f.write("#ifndef SECRETS_H\n#define SECRETS_H\n\n")

            for d in defines:
                f.write(f"{d}\n")
            
            f.write("\n// AWS IoT Certificates\n")
            f.write(f'static const char AWS_CERT_CA[] PROGMEM = R"EOF(\n{ca}\n)EOF";\n\n')
            f.write(f'static const char AWS_CERT_CRT[] PROGMEM = R"EOF(\n{crt}\n)EOF";\n\n')
            f.write(f'static const char AWS_CERT_PRIVATE[] PROGMEM = R"EOF(\n{key_content}\n)EOF";\n\n')

            f.write("\n#endif\n")
        
        print(f"--- secrets.h aggiornato da .env e /certs ---")
    except Exception as e:
        print(f"--- ERRORE sincronizzazione .env: {e} ---")

try:
    Import("env")
    sync(env.get("PROJECT_DIR"))
except Exception:
    if __name__ == "__main__":
        sync()
