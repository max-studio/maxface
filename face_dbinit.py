# coding = utf-8
import sqlite3
import base64


def init_db():
    sql = sqlite3.connect("sys_db.db")  # 建立数据库连接
    cur = sql.cursor()  # 得到游标对象
    cur.execute("""create table if not exists staff_tb(
        id int not null primary key,
        sname varchar(40) not null ,
        department varchar(40) not null
    ) """)
    cur.execute("""create table if not exists logcat_tb(
        id int not null primary key,
        clocktime text not null,
        latetime text not null
    )""")
    cur.execute("""create table if not exists admin_tb(
        id int not null primary key,
        adname varchar(40) not null,
        password varchar(30) not null
    )""")
    cur.execute("""create table if not exists face_tb(
        id int not null primary key,
        facearray array not null
    )""")
    cur.close()
    sql.commit()
    sql.close()


def insert_staff(id, name, depart):
    sql = sqlite3.connect("sys_db.db")
    cur = sql.cursor()
    cur.execute("insert into staff_tb(id,sname,department) values (?,?,?)", (id, name, depart))
    cur.close()
    sql.commit()
    sql.close()


def insert_admin(id, name, passwd):
    passwd_bs64 = base64.b64encode(passwd.encode("utf-8"))
    sql = sqlite3.connect("sys_db.db")
    cur = sql.cursor()
    cur.execute("insert into admin_tb(id,adname,password) values (?,?,?)", (id, name, passwd_bs64))
    cur.close()
    sql.commit()
    sql.close()


def insert_logcat(id, clock, late):
    sql = sqlite3.connect("sys_db.db")
    cur = sql.cursor()
    cur.execute("insert into logcat_tb(id,clocktime,latetime) values (?,?,?)", (id, clock, late))
    cur.close()
    sql.commit()
    sql.close()


def insert_face(id, face):
    sql = sqlite3.connect("sys_db.db")
    cur = sql.cursor()
    cur.execute("insert into face_tb(id,facearray) values (?,?)", (id, face))
    cur.close()
    sql.commit()
    sql.close()


def load_admin(id, passwd):
    passwd_bs64 = base64.b64encode(passwd.encode("utf-8"))
    sql = sqlite3.connect("sys_db.db")
    cur = sql.cursor()
    cur.execute("select id,adname,password from admin_tb where id = (?) and password = (?)", (id, passwd_bs64))
    # a= cur.fetchall()
    # for i in a:
    #     print(i)
    result = cur.fetchone()
    if result:
        return result[1]
    else:
        print("用户名或密码错误")


if __name__ == '__main__':
    init_db()
    # insert_staff(123456789, "张三", "人事部")
    # insert_admin(123456789, "张三", "abc123456")
    # insert_logcat(123456789, "2020-01-10 14:10:20", "20")
    load_admin(123456789, "abc123456")
