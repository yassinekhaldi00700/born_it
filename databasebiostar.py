import pyodbc
import pymysql

from config import env


def _clean_card(card_no):
    # "0494984137" -> "494984137"; keep "0" if the card is all zeros
    return str(card_no).strip().lstrip("0") or "0"


def swap_byte_order(decimal_number, bits=32):
    """Reverse the bytes of a card number (MSB <-> LSB). Same operation both ways.

    e.g. 3922684736 (0xE9D04040) <-> 1080807401 (0x4040D0E9)
    """
    masked_val = int(decimal_number) & ((1 << bits) - 1)
    return int.from_bytes(masked_val.to_bytes(bits // 8, "big"), "little")


# ---------- BioStar 1 (SQL Server) : teachers / staff ----------

def connect_biostar1():
    return pyodbc.connect(
        driver="{SQL Server}",
        server=env("BIOSTAR1_SERVER"),
        database=env("BIOSTAR1_DATABASE", "biostar"),
        uid=env("BIOSTAR1_USER"),
        pwd=env("BIOSTAR1_PASSWORD"),
        timeout=5,
    )


def _get_teacher(card_no):
    query = """
        SELECT TOP (1) a.sUserName, b.sFieldValue11, a.sEmail
        FROM TB_USER a
        INNER JOIN TB_USER_CUSTOMINFO b ON a.nUserIdn = b.nUserIdn
        INNER JOIN TB_USER_CARD c ON b.nUserIdn = c.nUserIdn
        WHERE c.sCardNo = ?
    """
    cnxn = connect_biostar1()
    try:
        row = cnxn.cursor().execute(query, card_no).fetchone()
    finally:
        cnxn.close()
    if row is None:
        return None
    return {"name": row[0], "id": row[1], "e-mail": row[2]}


# ---------- BioStar 2 (MySQL) : students ----------

def connect_biostar2():
    return pymysql.connect(
        host=env("BIOSTAR2_HOST"),
        port=int(env("BIOSTAR2_PORT", "3306")),
        database=env("BIOSTAR2_DATABASE", "biostar2_ac"),
        user=env("BIOSTAR2_USER"),
        password=env("BIOSTAR2_PASSWORD"),
        charset="utf8mb4",
        connect_timeout=5,
    )


def _get_student(card_no):
    # T_USRCUSFLD holds every custom field of a user; CUSFLDUID 1 = "Matricule" (see T_CUSFLDTYP)
    query = """
        SELECT u.NM, cf.VAL
        FROM T_USRCRD uc
        JOIN T_CRD c        ON c.CRDUID = uc.CRDUID
        JOIN T_USR u        ON u.USRUID = uc.USRUID
        JOIN T_USRCUSFLD cf ON cf.USRUID = uc.USRUID
        WHERE TRIM(LEADING '0' FROM c.CRDCSN) = %s
          AND cf.CUSFLDUID = %s
        ORDER BY u.CREATEDT DESC
        LIMIT 1
    """
    cnxn = connect_biostar2()
    try:
        with cnxn.cursor() as cursor:
            cursor.execute(query, (card_no, env("BIOSTAR2_MATRICULE_FIELD_ID", "1")))
            row = cursor.fetchone()
    finally:
        cnxn.close()
    if row is None:
        return None
    # Student e-mail comes from Konosys
    return {"name": row[0], "id": row[1], "e-mail": None}


def get_data(card_no, type):
    """Look up a card. type "S" = student (BioStar 2), anything else = teacher (BioStar 1).

    Returns {"name", "id", "e-mail"} with plain values, or None if not found.
    Database errors are raised so the caller can show them.
    """
    card_no = _clean_card(card_no)
    if type == "S":
        # Reader gives LSB, BioStar 2 stores the card in MSB form
        return _get_student(str(swap_byte_order(card_no)))
    return _get_teacher(card_no)


if __name__ == "__main__":
    print(get_data("494925769", "T"))
