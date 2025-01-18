import { Avatar } from "antd";
import MessageView from "./MessageView";


interface ChatContentType { // 聊天内容数据类型
    content: string;
    sendId: number;
    msgId: number;
    sender: string;
    avatar: string;
    replyId: number;
    replyMessage: ReplyContentType | null;
    ref?: React.RefObject<HTMLDivElement>;
}
interface ReplyContentType {

    content: string;
    senderName: string;

}

interface ReceiverItemProps {
    userName: string;
    item: ChatContentType;
    avatar: string;
    handleReplyItemClick: (item: ChatContentType) => void;
}

const SenderItem: React.FC<ReceiverItemProps> = ({ userName, item, avatar, handleReplyItemClick }) => {
    return (
        <div style={{ position: "relative", display: "flex", alignItems: "flex-start", justifyContent: "flex-end" }}>
            <div style={{ flex: 1, display: "flex", flexDirection: "column", justifyContent: "flex-end" }}>
                <MessageView type="text" isSender={true} item={item} />
                {item.replyId !== -1 && item.replyMessage && (
                    <div
                        style={{ marginTop: "10px", padding: "10px", background: "#f0f0f0", borderRadius: "4px", display: "flex", justifyContent: "flex-end", maxWidth: "50%", alignSelf: "flex-end" }}
                        onClick={() => {
                            console.log("点击回复，跳转到回复消息的位置");
                            handleReplyItemClick(item);
                        }}
                    >
                        <p style={{
                            margin: 0,
                            maxWidth: "200px",
                            overflow: "hidden",
                            textOverflow: "ellipsis",
                            whiteSpace: "nowrap"
                        }}>
                            <strong>{item.replyMessage.senderName}:</strong> {item.replyMessage.content}
                        </p>
                    </div>
                )}
            </div>
            <div style={{ width: "48px", marginLeft: "8px" }}>
                <Avatar src={avatar} size="large" style={{ backgroundColor: "#005EFF", verticalAlign: "middle" }}>
                </Avatar>
            </div>
        </div>
    );
};

export default SenderItem;

