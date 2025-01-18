import { useState } from "react";
import { BACKEND_URL, FAILURE_PREFIX, LOGIN_FAILED, REGISTER_SUCCESS_PREFIX } from "../constants/string";
import { useRouter } from "next/router";
import { setName, setToken } from "../redux/auth";
import { message } from "antd";
import { useDispatch } from "react-redux";
import styles from "../styles/LoginPage.module.css";

const RegisterScreen = () => {
    const [userName, setUserName] = useState("");
    const [password, setPassword] = useState("");
    const [errorMessage, setErrorMessage] = useState("");

    const router = useRouter();
    const dispatch = useDispatch();

    const register = () => {
        if (userName === "" || password === "") {
            message.error("用户名和密码不能为空");
            return;
        }
        fetch(`${BACKEND_URL}/api/author/register`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                userName,
                password,
            }),
        })
            .then((res) => res.json())
            .then((res) => {
                if (Number(res.code) === 0) {
                    dispatch(setName(userName));
                    dispatch(setToken(res.token));
                    message.success(REGISTER_SUCCESS_PREFIX + userName);
                    router.back();
                }
                else {
                    message.error("注册失败：" + res.info);
                }
            })
            .catch((err) => alert(FAILURE_PREFIX + err));
    };

    return (
        <div className={styles.container}>
            <h2>Register</h2>
            <form className={styles.form} onSubmit={(e) => e.preventDefault()}>
                <div className={styles.group}>
                    <label htmlFor="username">Username:</label><br />
                    <input
                        type="text"
                        id="username"
                        className={styles.control}
                        value={userName}
                        onChange={(e) => setUserName(e.target.value)}
                    />
                </div>
                <div className={styles.group}>
                    <label htmlFor="password">Password:</label><br />
                    <input
                        type="password"
                        id="password"
                        className={styles.control}
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                    />
                </div><br />
                {errorMessage && <div className={styles.error}>{errorMessage}</div>}
                <button className={`${styles.btn} ${styles.btnp}`} onClick={register}>
                    Register
                </button><br />
                <button className={`${styles.btn}`} onClick={() => router.back()}>
                    back to Login
                </button>
            </form>
        </div>
    );
};

export default RegisterScreen;
