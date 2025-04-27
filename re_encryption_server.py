from flask import Flask, request, jsonify
from umbral import SecretKey, Signer, encrypt, decrypt_reencrypted, generate_kfrags, pre
import umbral

app = Flask(__name__)

# 辅助函数：将密钥或Capsule等对象转换为十六进制字符串
def object_to_string(obj):
    return bytes(obj).hex()


# 辅助函数：将密钥换为十六进制字符串
def key_to_string(secret_key):
    # 将密钥转换为字节
    secret_bytes = secret_key.to_secret_bytes()
    # 转换为十六进制字符串
    secret_hex = secret_bytes.hex()
    # 保存到 .txt 文件
    # with open("secret_key.txt", "w") as f:
    #     f.write(secret_hex)
    return secret_hex

# 辅助函数：从十六进制字符串恢复密钥或Capsule等对象
def string_to_object(hex_string, obj_type):
    if obj_type == "SecretKey":
        return SecretKey.from_bytes(bytes.fromhex(hex_string))
    elif obj_type == "PublicKey":
        return umbral.PublicKey.from_bytes(bytes.fromhex(hex_string))
    elif obj_type == "Capsule":
        return umbral.Capsule.from_bytes(bytes.fromhex(hex_string))
    elif obj_type == "VerifiedCapsuleFrag":
        return pre.VerifiedCapsuleFrag.from_verified_bytes(bytes.fromhex(hex_string))
    elif obj_type == "KeyFrag":
        return pre.KeyFrag.from_bytes(bytes.fromhex(hex_string))
    else:
        raise ValueError("Unsupported object type")

# 1. 生成私钥
@app.route('/generate_secret_key', methods=['GET'])
def generate_secret_key():
    secret_key = SecretKey.random()
    return jsonify({
        "secret_key": key_to_string(secret_key)
    })

# 2. 使用私钥加密消息(先获取公钥，然后用公钥对信息加密)
@app.route('/encrypt_message', methods=['POST'])
def encrypt_message():
    data = request.json
    secret_key_hex = data.get("secret_key")
    message = data.get("message").encode("utf-8")

    if not secret_key_hex or not message:
        return jsonify({"error": "Missing secret_key or message"}), 400

    secret_key = string_to_object(secret_key_hex, "SecretKey")
    public_key = secret_key.public_key()
    capsule, ciphertext = encrypt(public_key, message)
    return jsonify({
        "capsule": object_to_string(capsule),
        "ciphertext": ciphertext.hex()
    })

# 3. 直接使用私钥解密密文（secret_key，capsule，ciphertext）
@app.route('/decrypt_message', methods=['POST'])
def decrypt_message():
    data = request.json
    a_secret_key_hex = data.get("secret_key")
    capsule_hex = data.get("capsule")
    ciphertext_hex = data.get("ciphertext")

    if not a_secret_key_hex or not capsule_hex or not ciphertext_hex:
        return jsonify({"error": "Missing keys or ciphertext"}), 400

    a_secret_key = string_to_object(a_secret_key_hex, "SecretKey")
    a_public_key = a_secret_key.public_key()

    capsule = string_to_object(capsule_hex, "Capsule")
    ciphertext = bytes.fromhex(ciphertext_hex)

    try:
        cleartext = decrypt_reencrypted(
            receiving_sk=a_secret_key,
            delegating_pk=a_public_key,
            capsule=capsule,
            verified_cfrags=[],  # 设置为空列表
            ciphertext=ciphertext
        )
        return jsonify({
            "cleartext": cleartext.decode("utf-8")
        })
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:  # 添加捕获其他异常
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

# 4. 生成重加密密钥(A的私钥，B的公钥(用于获取B的私钥)，A的签名器(用A的私钥获取))
@app.route('/generate_reencryption_key', methods=['POST'])
def generate_reencryption_key():
    data = request.json
    a_secret_key_hex = data.get("a_secret_key")
    b_secret_key_hex = data.get("b_secret_key")

    if not a_secret_key_hex or not b_secret_key_hex:
        return jsonify({"error": "Missing keys"}), 400

    a_secret_key = string_to_object(a_secret_key_hex, "SecretKey")
    b_secret_key = string_to_object(b_secret_key_hex, "SecretKey")
    a_signer = Signer(a_secret_key)

    b_public_key = b_secret_key.public_key()
    kfrag = generate_kfrags(
        delegating_sk=a_secret_key,
        receiving_pk=b_public_key,
        signer=a_signer,
        threshold=1,
        shares=1
    )[0]
    return jsonify({
        "kfrag": object_to_string(kfrag)
    })


# 5. 重加密Capsule(需要a公钥(通过a私钥获取)，需要b公钥(通过b私钥获取)，需要a加密后的capsule, 重加密密钥)
@app.route('/reencrypt_capsule', methods=['POST'])
def reencrypt_capsule():
    data = request.json
    a_secret_key_hex = data.get("a_secret_key")
    b_secret_key_hex = data.get("b_secret_key")
    capsule_hex = data.get("capsule")
    kfrag_hex = data.get("kfrag")

    if not a_secret_key_hex or not b_secret_key_hex or not capsule_hex or not kfrag_hex:
        return jsonify({"error": "Missing a_secret_key_hex or b_secret_key_hex or capsule or kfrag"}), 400
    
    a_secret_key = string_to_object(a_secret_key_hex, "SecretKey")
    a_public_key = a_secret_key.public_key()
    b_secret_key = string_to_object(b_secret_key_hex, "SecretKey")
    b_public_key = b_secret_key.public_key()
    capsule = umbral.Capsule.from_bytes(bytes.fromhex(capsule_hex))
    kfrag = pre.KeyFrag.from_bytes(bytes.fromhex(kfrag_hex))

    # 验证 kfrag
    try:
        verified_kfrag = kfrag.verify(
            delegating_pk=a_public_key,
            receiving_pk=b_public_key,
            verifying_pk=a_public_key
        )
    except Exception as e:
        return jsonify({"error": f"Failed to verify kfrag: {str(e)}"}), 400

    if not verified_kfrag:
        return jsonify({"error": "kfrag verification failed"}), 400

    cfrag = pre.reencrypt(capsule=capsule, kfrag=verified_kfrag)
    return jsonify({
        "cfrag": object_to_string(cfrag)
    })

# 6. 解密重加密后的Capsule(需要A私钥，B私钥，重加密密钥，重加密后的Capsule)
@app.route('/decrypt_reencrypted_capsule', methods=['POST'])
def decrypt_reencrypted_capsule():
    data = request.json
    b_secret_key_hex = data.get("b_secret_key")
    a_secret_key_hex = data.get("a_secret_key")
    capsule_hex = data.get("capsule")
    cfrag_hex = data.get("cfrag")
    ciphertext_hex = data.get("ciphertext")

    if not b_secret_key_hex or not a_secret_key_hex or not capsule_hex or not cfrag_hex or not ciphertext_hex:
        return jsonify({"error": "Missing keys or ciphertext"}), 400

    b_secret_key = string_to_object(b_secret_key_hex, "SecretKey")
    a_secret_key = string_to_object(a_secret_key_hex, "SecretKey")
    a_public_key = a_secret_key.public_key()

    capsule = string_to_object(capsule_hex, "Capsule")
    cfrag = string_to_object(cfrag_hex, "VerifiedCapsuleFrag")
    ciphertext = bytes.fromhex(ciphertext_hex)

    cleartext = decrypt_reencrypted(
        receiving_sk=b_secret_key,
        delegating_pk=a_public_key,
        capsule=capsule,
        verified_cfrags=[cfrag],
        ciphertext=ciphertext
    )
    return jsonify({
        "cleartext": cleartext.decode("utf-8")
    })


if __name__ == '__main__':
    # app.run(debug=True)
    print("hhhhhhhhhhhhhhhhhhh")
    app.run(host='0.0.0.0', port=9091)