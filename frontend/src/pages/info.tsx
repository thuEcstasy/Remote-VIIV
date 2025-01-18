import React, { useState, useEffect } from "react";
import styles from "../styles/LoginPage.module.css";
import { useRouter } from "next/router";
import { BACKEND_URL, FAILURE_PREFIX, AVATAR_UPLOAD_FAILED } from "../constants/string";
import SiderBar from "../components/SiderBar";
import store from "../redux/store";
import { PlusOutlined, UserOutlined } from "@ant-design/icons";
import type { GetProp, UploadFile, UploadProps, DatePickerProps } from "antd";
import { Layout, Image, Upload, Input, DatePicker, Space, Button, message, Avatar, Modal, Form } from "antd";
import { useDispatch } from "react-redux";
import { setName, setToken, setEmail, setPhone, setAvatar, setId } from "../redux/auth";


/* 头像上传 */
type FileType = Parameters<GetProp<UploadProps, "beforeUpload">>[0];

const getBase64 = (file: FileType): Promise<string> =>
    new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.readAsDataURL(file);
        reader.onload = () => resolve(reader.result as string);
        reader.onerror = (error) => reject(error);
    });

/* 用户信息 */
interface UserInfo {
    name: string;
    email: string;
    phone: string;
    email_code: string;
    phone_code: string;
    avatar: string;
}

const UserInfoPage: React.FC = () => {
    const router = useRouter();
    const dispatch = useDispatch();
    const [password, setPassword] = useState("");

    const [clickEmailCode, setClickEmailCode] = useState(false);
    const [emailcountdown, setEmailCountdown] = useState(180); //初始倒计时时间为180秒

    const [clickPhoneCode, setClickPhoneCode] = useState(false);
    const [phonecountdown, setPhoneCountdown] = useState(180); //初始倒计时时间为180秒

    const [previewOpen, setPreviewOpen] = useState(false);
    const [previewImage, setPreviewImage] = useState("");
    const [fileList, setFileList] = useState<UploadFile[]>([]);
    const [avatar, setAvatarr] = useState<string>(store.getState().auth.avatar);

    const auth = store.getState().auth;
    const name = auth && auth.name ? auth.name : "";
    const email = auth && auth.email ? auth.email : "";
    const phone = auth && auth.phone ? auth.phone : "";

    const [userInfo, setUserInfo] = useState<UserInfo>({
        name,
        email,
        phone,
        email_code: "",
        phone_code: "",
        avatar,
    });

    /* 引入输入框的文本 */
    const handleChange = (e: React.ChangeEvent<HTMLInputElement>, field: keyof UserInfo) => {
        setUserInfo({ ...userInfo, [field]: e.target.value });
    };

    /* 保存更新的用户信息 */
    const handleEmailSave = async () => {
        const token = `${store.getState().auth.token}`;
        console.log(token);
        console.log(userInfo);
        //邮箱
        if (userInfo.email === "") {
            message.error("邮箱不能为空");
        }
        else {
            try {
                const url = `${BACKEND_URL}/api/author/email/verification/verify`;
                const method = "POST";
                const headers = {
                    "Content-Type": "application/json",
                    "Authorization": token,
                };
                const body = JSON.stringify({
                    code: userInfo.email_code,
                    email: userInfo.email
                });
                // 打印请求信息到控制台
                console.log("Sending request:");
                console.log("URL:", url);
                console.log("Method:", method);
                console.log("Headers:", headers);
                console.log("Body:", body);
                console.log(userInfo.phone);
                const response = await fetch(url, {
                    method,
                    headers,
                    body,
                });
                const res = await response.json();
                if (Number(res.code) === 0) {
                    message.success("邮箱更新成功");
                    setUserInfo(prevState => ({
                        ...prevState,
                        email: userInfo.email,
                        email_code: userInfo.email_code,
                    }));
                    dispatch(setEmail(userInfo.email));
                }
                else {
                    message.error("邮箱 " + res.code + " " + res.info);
                }
            }
            catch (err) {
                console.error(err);
                message.error("邮箱更新错误：" + err);
            }
        }
    };
    const handlePhoneSave = async () => {
        if (userInfo.phone === "") {
            message.error("手机不能为空");
        }
        else {
            try {
                const response = await fetch(`${BACKEND_URL}/api/author/number/verification/verify`, {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "Authorization": `${store.getState().auth.token}`,
                    },
                    body: JSON.stringify({
                        code: userInfo.phone_code,
                        number: userInfo.phone,
                    }),
                });
                const res = await response.json();
                if (Number(res.code) === 0) {
                    message.success("手机更新成功");
                    setUserInfo(prevState => ({
                        ...prevState,
                        phone: userInfo.phone,
                        phone_code: userInfo.phone_code,
                    }));
                    dispatch(setPhone(userInfo.phone));
                }
                else {
                    message.error(res.code + " " + res.info);
                }
            }
            catch (err) {
                message.error("手机更新错误：" + err);
            }
        }
    };
    /* 设置邮箱和手机验证码倒计时 */
    useEffect(() => {
        if (emailcountdown === 0) {
            setEmailCountdown(180);
            setClickEmailCode(false);
        }
    }, [emailcountdown]);

    useEffect(() => {
        if (phonecountdown === 0) {
            setPhoneCountdown(180);
            setClickPhoneCode(false);
        }
    }, [phonecountdown]);

    const startEmailCountdown = () => {
        setClickEmailCode(true);
        const intervalId = setInterval(() => {
            setEmailCountdown(prevCountdown => prevCountdown - 1);
        }, 1000);
        return () => clearInterval(intervalId);
    };

    const startPhoneCountdown = () => {
        setClickPhoneCode(true);
        const intervalId = setInterval(() => {
            setPhoneCountdown(prevCountdown => prevCountdown - 1);
        }, 1000);
        return () => clearInterval(intervalId);
    };

    /* 获取邮箱验证码 */
    const handleEmailCode = async () => {
        await fetch(`${BACKEND_URL}/api/author/email/verification/send`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `${store.getState().auth.token}`,
            },
            body: JSON.stringify({
                email: userInfo.email,
            }),
        })
            .then((res) => res.json())
            .then((res) => {
                if (Number(res.code) === 0) {
                    message.success("成功获取邮箱验证码");
                    startEmailCountdown();
                }
                else {
                    message.error(res.code + " " + res.info);
                }
            })
            .catch((err) => message.error(err));
    };

    /* 获取手机验证码 */
    const handlePhoneCode = async () => {
        startPhoneCountdown();
        await fetch(`${BACKEND_URL}/api/author/number/verification/send`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `${store.getState().auth.token}`,
            },
            body: JSON.stringify({
                number: userInfo.phone
            }),
        })
            .then((res) => res.json())
            .then((res) => {
                if (Number(res.code) === 0) {
                    message.success("成功获取手机验证码");
                }
                else {
                    message.error(res.code + " " + res.msg);
                }
            })
            .catch((err) => message.error(err));
    };

    /* 侧边栏切换 */
    const handleItemClick = ({ key }: { key: string }) => {
        switch (key) {
            case "1":
                router.push("/main");
                break;
            case "2":
                break;
            case "3":
                router.push("/grouplist");
                break;
            case "4":
                router.push("/friendslist");
                break;
            case "5":
                break;
            default:
                break;
        }
    };

    /* 头像预览 */
    const handlePreview = async (file: UploadFile) => {
        if (!file.url && !file.preview) {
            file.preview = await getBase64(file.originFileObj as FileType);
        }

        setPreviewImage(file.url || (file.preview as string));
        setPreviewOpen(true);

    };

    /* 更新头像申请 */
    const handleChange_photo: UploadProps["onChange"] = async ({ fileList: newFileList }) => {
        setFileList(newFileList);

        if (newFileList.length > 0) {
            const base64String: string = await getBase64(newFileList[0].originFileObj as FileType);

            await fetch(`${BACKEND_URL}/api/author/avatar/update`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `${store.getState().auth.token}`,
                },
                body: JSON.stringify({
                    avatar: base64String
                }),
            })
                .then((res) => res.json())
                .then((res) => {
                    if (Number(res.code) === 0) {
                        message.success("头像更新成功");
                        setAvatarr(base64String);
                        dispatch(setAvatar(base64String));
                    }
                    else {
                        message.error(res.code + " " + res.info);
                    }
                })
                .catch((err) => message.error(AVATAR_UPLOAD_FAILED + err));
        }
    };

    /* 上传按钮组件 */
    const uploadButton = (
        <button style={{ border: 0, background: "none" }} type="button">
            <PlusOutlined />
            <div style={{ marginTop: 8 }}>Upload</div>
        </button>
    );

    /* 登出 */
    const handleLogout = async () => {
        await fetch(`${BACKEND_URL}/api/author/logout`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `${store.getState().auth.token}`,
            },
        })
            .then((res) => res.json())
            .then((res) => {
                if (Number(res.code) === 0) {
                    message.success("成功登出");
                    router.push("/");
                }
                else {
                    message.error("登出失败");
                }
            })
            .catch((err) => message.error(FAILURE_PREFIX + err));
    };

    /* 处理用户名修改 */
    const [isNameModalVisible, setIsNameModalVisible] = useState(false);
    const [newName, setNewName] = useState<string>("");

    const handleNameChange = async () => {
        console.log("newName:", newName);
        await fetch(`${BACKEND_URL}/api/author/change/name`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `${store.getState().auth.token}`,
            },
            body: JSON.stringify({
                new_name: newName
            }),
        })
            .then((res) => res.json())
            .then((res) => {
                if (Number(res.code) === 0) {
                    message.success("成功更改用户名");
                    dispatch(setName(newName));
                    setUserInfo({ ...userInfo, ["name"]: newName });
                    dispatch(setToken(res.token));
                }
                else {
                    message.error(res.code + " " + res.info);
                }
            })
            .catch((err) => message.error(err));
    };

    /* 处理删除账号操作 */
    const [isDelModalVisible, setIsDelModalVisible] = useState(false);

    const delete_account = async () => {
        await fetch(`${BACKEND_URL}/api/author/delete`, {
            method: "DELETE",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `${store.getState().auth.token}`,
            },
            body: JSON.stringify({
                password,
            }),
        })
            .then((res) => res.json())
            .then((res) => {
                if (Number(res.code) === 0) {
                    message.success("账户删除成功");
                    router.push("/");
                }
                else {
                    message.error("删除账户失败");
                }
            })
            .catch((err) => message.error(FAILURE_PREFIX + err));
    };

    /* 改密码 */
    const [isChangePasswordModalVisible, setIsChangePasswordModalVisible] = useState(false);
    const [oldPassword, setOldPassword] = useState("");
    const [newPassword, setNewPassword] = useState("");

    const change_password = async () => {
        await fetch(`${BACKEND_URL}/api/author/change/password`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `${store.getState().auth.token}`,
            },
            body: JSON.stringify({
                old_password: oldPassword,
                new_password: newPassword,
            }),
        })
            .then((res) => res.json())
            .then((res) => {
                if (Number(res.code) === 0) {
                    message.success("密码修改成功");
                }
                else {
                    message.error("密码修改失败");
                }
            })
            .catch((err) => message.error("密码修改失败：" + err));
    };

    return (
        <>
            <Layout style={{ minHeight: "95vh" }}>
                <SiderBar defaultKey={"5"} handleItemClick={handleItemClick}>
                    <div className="demo-logo-vertical" />
                </SiderBar>

                <div className="container" style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center" }}>
                    <Avatar size={128} src={avatar}>
                    </Avatar>
                    <Form
                        labelCol={{ span: 4 }}
                        wrapperCol={{ span: 14 }}
                        layout="horizontal"
                        style={{ maxWidth: 600 }}
                    >
                        <Form.Item label="Name">
                            <Input size="large" placeholder="User Name" prefix={<UserOutlined />} value={userInfo.name} onChange={(e) => handleChange(e, "name")}>
                            </Input>
                            <Button className={`${styles.btn} ${styles.btnp}`} onClick={() => setIsNameModalVisible(true)}>
                                Change Name
                            </Button>
                            <Modal
                                footer={null}
                                title="修改用户名"
                                open={isNameModalVisible}
                                onCancel={() => setIsNameModalVisible(false)}
                                style={{ display: "flex", flexDirection: "column" }}>
                                <div >
                                    <Input
                                        placeholder="new name"
                                        className={styles.control}
                                        prefix={<UserOutlined />}
                                        value={newName}
                                        onChange={(e) => setNewName(e.target.value)}
                                    />
                                </div>
                                <br />
                                <Button onClick={handleNameChange}>
                                    确认修改
                                </Button>
                            </Modal>
                        </Form.Item>
                        <Form.Item label="Password">
                            <Button className={`${styles.btn}`} onClick={() => setIsChangePasswordModalVisible(true)}>
                                Change Password
                            </Button>
                            <Modal
                                footer={null}
                                title="修改密码"
                                open={isChangePasswordModalVisible}
                                onCancel={() => setIsChangePasswordModalVisible(false)}
                                style={{ display: "flex", flexDirection: "column" }}>
                                <div style={{ display: "flex", flexDirection: "column" }}>
                                    <Input
                                        type="old_password"
                                        id="old_password"
                                        placeholder="old password"
                                        className={styles.control}
                                        prefix={<UserOutlined />}
                                        value={oldPassword}
                                        onChange={(e) => setOldPassword(e.target.value)}
                                    />
                                    <Input
                                        type="new_password"
                                        id="new_password"
                                        placeholder="new password"
                                        className={styles.control}
                                        prefix={<UserOutlined />}
                                        value={newPassword}
                                        onChange={(e) => setNewPassword(e.target.value)}
                                    />
                                </div>
                                <br />
                                <Button onClick={change_password}>
                                    确认修改
                                </Button>
                            </Modal>
                        </Form.Item>
                        <Form.Item label="Email">
                            <Input size="large" placeholder="Email" prefix={<UserOutlined />} value={userInfo.email} onChange={(e) => handleChange(e, "email")}>
                            </Input>
                            <Input size="large" placeholder="verification code" prefix={<UserOutlined />} value={userInfo.email_code} onChange={(e) => handleChange(e, "email_code")}>
                            </Input>
                            <Button className={`${styles.btn} ${styles.btnp}`} onClick={handleEmailCode} disabled={clickEmailCode}>{clickEmailCode ? `${emailcountdown} 秒后重新获取` : "获取验证码"}
                            </Button>
                            <Button className={`${styles.btn} ${styles.btnp}`} onClick={handleEmailSave}>
                                Save Email
                            </Button>
                        </Form.Item>
                        <Form.Item label="Phone Number">
                            <Input size="large" placeholder="Phone Number" prefix={<UserOutlined />} value={userInfo.phone} onChange={(e) => handleChange(e, "phone")}>
                            </Input>
                            <Input size="large" placeholder="verification code" prefix={<UserOutlined />} value={userInfo.phone_code} onChange={(e) => handleChange(e, "phone_code")} >
                            </Input>
                            <Button className={`${styles.btn} ${styles.btnp}`} onClick={handlePhoneCode} disabled={clickPhoneCode}>{clickPhoneCode ? `${phonecountdown} 秒后重新获取` : "获取验证码"}
                            </Button>
                            <Button className={`${styles.btn} ${styles.btnp}`} onClick={handlePhoneSave}>
                                Save Phone
                            </Button>
                        </Form.Item>
                        <Form.Item label="Change Avatar">
                            <Upload
                                action="https://660d2bd96ddfa2943b33731c.mockapi.io/api/upload"
                                listType="picture-circle"
                                fileList={fileList}
                                onPreview={handlePreview}
                                onChange={handleChange_photo}
                            >
                                {fileList.length >= 1 ? null : uploadButton}
                                {/* {uploadButton} */}
                            </Upload>
                            {previewImage && (
                                <Image
                                    wrapperStyle={{ display: "none" }}
                                    preview={{
                                        visible: previewOpen,
                                        onVisibleChange: (visible) => setPreviewOpen(visible),
                                        afterOpenChange: (visible) => !visible && setPreviewImage(""),
                                    }}
                                    src={previewImage}
                                    alt="Preview Image"
                                />
                            )}
                        </Form.Item>
                    </Form>

                    <Button className={`${styles.btn}`} onClick={handleLogout} >
                        Logout
                    </Button><br />
                    <Button className={`${styles.btn}`} onClick={() => setIsDelModalVisible(true)} danger>
                        Delete Account
                    </Button>
                    <Modal
                        footer={null}
                        title="账号删除确认"
                        open={isDelModalVisible}
                        onCancel={() => setIsDelModalVisible(false)}
                        style={{ display: "flex", flexDirection: "column" }}>
                        <div >
                            <Input
                                type="password"
                                id="password"
                                placeholder="password"
                                className={styles.control}
                                prefix={<UserOutlined />}
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                            />
                        </div>
                        <br />
                        <Button onClick={delete_account} danger>
                            确认删除
                        </Button>
                    </Modal>


                </div>
            </Layout>
        </>
    );

};

export default UserInfoPage;