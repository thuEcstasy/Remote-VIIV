import cls from "classnames";
// import moment from 'moment';

// import styles from "../styles/MessageStyle.module.less";
// import { SettingOutlined } from "@ant-design/icons";
import moreSvg from "./more.svg";

const MESSAGE_TYPE_IMAGE = "image";
const MESSAGE_TYPE_TEXT = "text";

interface ChatContentType {
    content: string;
    sendId: number;
    msgId: number;
    sender: string;
}

interface MessageProps {
    isSender: boolean;
    type: string;
    item: ChatContentType;
}

const MessageView: React.FC<MessageProps> = ({ isSender, type, item }) => {
    // console.log('MessageView :: ', item);

    const content = item.content;

    const renderPopuMenuSender = () => {
        return (
            <div style={{
                width: "16px",
                height: "16px",
                cursor: "pointer",
                opacity: 0,
                marginRight: "8px"
            }}>
                <img style={{ width: "100%", height: "100%" }} src={moreSvg} />
            </div>
        );
    };

    const renderPopuMenuReceiver = () => {
        return (
            <div style={{
                width: "16px",
                height: "16px",
                cursor: "pointer",
                opacity: 0,
                marginLeft: "8px"
            }}>
                <img style={{ width: "100%", height: "100%" }} src={moreSvg} />
            </div>
        );
    };

    const renderMessageView = () => {
        // 文本消息
        if (type === MESSAGE_TYPE_TEXT) {
            if (isSender) {
                return <div style={{
                    width: "fit-content",
                    maxWidth: "500px",
                    padding: "8px",
                    overflow: "hidden",
                    fontSize: "14px",
                    whiteSpace: "break-spaces",
                    textOverflow: "ellipsis",
                    backgroundColor: "lavender"
                }}>{content}</div>;
            }
            else {
                return <div style={{
                    width: "fit-content",
                    maxWidth: "500px",
                    padding: "8px",
                    overflow: "hidden",
                    fontSize: "14px",
                    whiteSpace: "break-spaces",
                    textOverflow: "ellipsis",
                    backgroundColor: "aliceblue"
                }}>{content}</div>;
            }
        }

        // 图片消息
        if (type === MESSAGE_TYPE_IMAGE) {
            return (
                <div style={{
                    maxWidth: "128px",
                    maxHeight: "128px",
                    padding: "8px",
                    backgroundColor: "aliceblue"
                }}>
                    <img style={{ width: "100%", height: "100%" }} src={content} />
                </div>
            );
        }

        return null;
    };

    if (isSender) {
        // 发送消息
        return (
            <div style={{ position: "relative", width: "100 %", minHeight: "48px" }}>
                <div style={{
                    padding: "0 8px 8px 8px",
                    overflow: "hidden",
                    whiteSpace: "pre",
                    textAlign: "left",
                    wordWrap: "break-word",
                    wordBreak: "break-all",
                    cursor: "default",
                    display: "flex",
                    flexDirection: "column",
                    alignItems: "flex-end"
                }}>
                    {/* <div className={messageTimeStyle}>{moment(sendTime).format('LTS')}</div> */}
                    <div style={{ display: "flex", alignItems: "flex-end", justifyContent: "flex-end" }}>
                        {isSender && renderPopuMenuSender()}
                        {renderMessageView()}
                    </div>
                </div>
            </div>
        );
    }

    else {
        // 接收消息
        return (
            <div style={{ position: "relative", width: "100 %", minHeight: "48px" }}>
                <div style={{
                    padding: "0 8px 8px 8px",
                    overflow: "hidden",
                    whiteSpace: "pre",
                    textAlign: "left",
                    wordWrap: "break-word",
                    wordBreak: "break-all",
                    cursor: "default",
                    display: "flex",
                    flexDirection: "column",
                    alignItems: "flex-start"
                }}>
                    {/* <div className={messageTimeStyle}>{moment(sendTime).format('LTS')}</div> */}
                    <div style={{ display: "flex", alignItems: "flex-end", justifyContent: "flex-start" }}>
                        {!isSender && renderPopuMenuReceiver()}
                        {renderMessageView()}
                    </div>
                </div>
            </div>
        );
    }

};

export default MessageView;