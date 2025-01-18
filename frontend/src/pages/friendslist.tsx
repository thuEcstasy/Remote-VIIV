
import React, { useState, useEffect, useRef } from "react";
import { useRouter } from "next/router";
import { PieChartOutlined, UserAddOutlined, PlusOutlined, TeamOutlined, AppstoreOutlined } from "@ant-design/icons";
import type { InputRef } from "antd";
import { Checkbox, Select, Breadcrumb, Flex, Tooltip, Layout, message, Tag, theme, Input, Avatar, Button, List, Badge, Divider, Col, Drawer, Row } from "antd";
import SiderBar from "../components/SiderBar";
import { BACKEND_URL } from "../constants/string";
import store from "../redux/store";


const { Sider, Header, Content } = Layout;
const { Search } = Input;

interface DescriptionItemProps {
    title: string;
    content: React.ReactNode;
}

const DescriptionItem = ({ title, content }: DescriptionItemProps) => (
    <div className="site-description-item-profile-wrapper">
        <p className="site-description-item-profile-p-label">{title}:</p>
        {content}
    </div>
);

/* 搜索添加好友列表 */
interface FriendsDataType {
    name: string;
    avatar: string;
    sendStatus: string;
    id: number;
    status: number;
}

type PaginationPosition = "top" | "bottom" | "both";
type PaginationAlign = "start" | "center" | "end";

/* 标签 */
const tagInputStyle: React.CSSProperties = {
    width: 64,
    height: 22,
    marginInlineEnd: 8,
    verticalAlign: "top",
};


const ListPage: React.FC = () => {
    const router = useRouter();
    const [loading, setLoading] = useState(false);
    const [myFriends, setMyFriends] = useState<FriendsDataType[]>([]); //好友列表
    const [userdata, setUserData] = useState<FriendsDataType[]>([]); //搜索的用户列表
    const [position, setPosition] = useState<PaginationPosition>("bottom");
    const [align, setAlign] = useState<PaginationAlign>("center");
    const [searchUser, setSearchUser] = useState<string>("");
    const [open, setOpen] = useState(false); // 抽屉，展示详细的好友信息
    const [childrenDrawer, setChildrenDrawer] = useState(false); // 二级抽屉，添加标签
    const [UnackList, setUnackList] = useState(false); // 抽屉，展示待通过的好友申请列表
    const [CreateGroupList, setCreateGroupList] = useState(false);
    const [unack, setUnAck] = useState<FriendsDataType[]>([]); // 待通过的好友申请列表
    const [toAccept, setToAccept] = useState<number>(-1); // 处理好友申请
    const [AckRefuse, setAckRefuse] = useState<string>(""); //接受或拒绝好友申请
    const [FriendsProfile, setFriendsProfile] = useState<FriendsDataType>(); // 好友详细信息
    const [UserProfile, setUserProfile] = useState<number>(-1); // 用户详细信息
    const [selectedFriends, setSelectedFriends] = useState<number[]>([]);
    const [groupName, setGroupName] = useState("");

    /* 根据不同的菜单项key执行不同的操作 */
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
                break;
            case "5":
                router.push("/info");
                break;
            default:
                break;
        }
    };

    /* 初始化好友列表 */
    useEffect(() => {
        if (UnackList) {
            return;
        }
        if (open) {
            return;
        }


        ToAcceptList(); // 待通过的好友申请列表

        const fetchFriends = async () => {
            console.log("开始获取好友列表");
            try {
                const response = await fetch(`${BACKEND_URL}/api/friends/friend/list_all`, {
                    method: "GET",
                    headers: {
                        Authorization: `${store.getState().auth.token}`,
                    },
                });

                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }

                const bodys = await response.json();

                if (bodys.code === 0) {
                    const friList: FriendsDataType[] = [];
                    for (const body of bodys.members) {
                        console.log(body);
                        const myfri: FriendsDataType = {
                            name: body.username,
                            avatar: body.avatar,
                            id: body.id,
                            status: body.status, // 待修改
                            sendStatus: "", // 待修改
                        };
                        if (myfri.status === 0) {
                            myfri.sendStatus = "send request";
                        }
                        else if (myfri.status === 1) {
                            myfri.sendStatus = "already friend";
                        }
                        else if (myfri.status === 2) {
                            myfri.sendStatus = "waiting for response";
                        }
                        friList.push(myfri);
                    }
                    setMyFriends([...friList]); //后期改成请求
                    console.log("我的好友初始化成功");
                    console.log(friList);

                }
                else {
                    console.error("获取好友列表失败:", bodys.code, bodys.info);
                }
            }
            catch (err) {
                console.error("获取好友列表时发生错误:", err);
            }
        };

        fetchFriends();
    }, [UnackList, open]);


    /* 搜索用户列表处理 */
    const searchFriends = () => {
        console.log("searchFriends");
        if (loading) {
            return;
        }
        setLoading(true);

        const params = {
            query: searchUser,
        };
        const queryString = new URLSearchParams(params).toString();
        const urlforsearch = `${BACKEND_URL}/api/friends/search/user?${queryString}`;

        fetch(urlforsearch, {
            method: "GET",
            headers: {
                Authorization: `${store.getState().auth.token}`,
            },
        })
            .then((res) => res.json())
            .then((bodys) => {
                console.log("接收到了返回");
                const userrList: FriendsDataType[] = [];
                for (const body of bodys) {
                    const uuunack: FriendsDataType = {
                        name: body.name,
                        avatar: body.avatar,
                        id: body.id,
                        status: body.status, // 待修改
                        sendStatus: "", // 待修改
                    };
                    console.log(uuunack); // 输出搜索到的用户列表
                    if (uuunack.status === 0) {
                        uuunack.sendStatus = "send request";
                    }
                    else if (uuunack.status === 1) {
                        uuunack.sendStatus = "already friend";
                    }
                    else if (uuunack.status === 2) {
                        uuunack.sendStatus = "waiting for response";
                    }
                    userrList.push(uuunack);
                }
                setUserData([...userrList]);
                console.log("搜索到的用户列表userdata添加成功");
                setLoading(false);
            })
            .catch((err) => {
                setLoading(false);
                alert("获取错误：" + err);
            });
    };

    /* 发送好友请求 */
    useEffect(() => {
        if (UserProfile === -1) {
            return;
        }
        console.log("id:" + UserProfile);
        sendFriendsRequest();
    }, [UserProfile]);

    const sendFriendsRequest = async () => {
        console.log("sendFriendsRequest");
        await fetch(`${BACKEND_URL}/api/friends/request/friend`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `${store.getState().auth.token}`,
            },
            body: JSON.stringify({
                to_user_id: UserProfile,
            }),
        })
            .then((res) => res.json())
            .then((res) => {
                console.log("发送好友请求成功");
                if (Number(res.code) === 0) {
                    message.success("申请发送成功");
                    console.log("fasong好友请求chenggong");
                }
                else {
                    alert(res.code + " " + res.info);
                    console.log("fasong好友请求失败:" + UserProfile);
                }
            })
            .catch((err) => alert("申请发送错误：" + err));
    };

    /* 待通过的好友申请列表 */
    const ToAcceptList = async () => {
        // setUnackList(true);

        await fetch(`${BACKEND_URL}/api/friends/require/friend`, {
            method: "GET",
            headers: {
                Authorization: `${store.getState().auth.token}`,
            },
        })
            .then((res) => res.json())
            .then((ress) => {
                if (Number(ress.code) === 0) {
                    console.log("能够获取到待通过的好友申请列表");
                    const uunackList: FriendsDataType[] = [];
                    for (const res of ress.requests) {
                        const uuunack: FriendsDataType = {
                            name: res.from_user_name,
                            avatar: res.from_user_avatar,
                            id: res.id,
                            status: 0,
                            sendStatus: "",
                        };
                        uunackList.push(uuunack);
                    }
                    setUnAck([...uunackList]);
                    console.log("unackList添加成功");
                    setLoading(false); //不需要吧
                }
                else {
                    alert(ress.code + " " + ress.info);
                }
            })
            .catch((err) => {
                alert("获取错误：" + err);
                console.log("unackList添加失败");
            });
    };
    /* 通过申请 */
    useEffect(() => {
        if (toAccept === -1) {
            return;
        }
        acceptFriend();
    }, [toAccept]);
    const acceptFriend = async () => {
        console.log(toAccept.toString());
        await fetch(`${BACKEND_URL}/api/friends/request/friend/handle`, {
            method: "POST",
            headers: {
                Authorization: `${store.getState().auth.token}`,
            },
            body: JSON.stringify({
                request_id: toAccept.toString(),
                action: AckRefuse,
            }),
        })
            .then((res) => res.json())
            .then((res) => {
                if (Number(res.code) === 0) {
                    console.log("能够处理好友申请");
                    if (AckRefuse === "accept") {
                        message.success("好友申请已通过");
                    }
                    else {
                        message.success("好友申请已拒绝");
                    }
                }
                else {
                    message.error(res.code + " " + res.info);
                }
            })
            .catch((err) => message.error("处理好友申请失败"));
    };

    /* 删除好友 */
    const deleteFriend = async () => {
        await fetch(`${BACKEND_URL}/api/friends/delete/friend`, {
            method: "DELETE",
            headers: {
                Authorization: `${store.getState().auth.token}`,
            },
            body: JSON.stringify({
                to_user: FriendsProfile?.name,
            }),
        })
            .then((res) => res.json())
            .then((res) => {
                if (Number(res.code) === 0) {
                    message.success("好友删除成功");
                }
                else {
                    message.error(res.code + " " + res.info);
                    console.log("删除好友失败");
                }
            })
            .catch((err) => alert("删除错误：" + err));
    };


    /* 添加标签 */
    const { token } = theme.useToken();
    const [tags, setTags] = useState<string[]>([]);
    const [inputVisible, setInputVisible] = useState(false);
    const [inputValue, setInputValue] = useState("");
    const [editInputIndex, setEditInputIndex] = useState(-1); // 编辑已有标签的索引
    const [editInputValue, setEditInputValue] = useState(""); // 编辑已有标签的输入值
    const inputRef = useRef<InputRef>(null);
    const editInputRef = useRef<InputRef>(null);
    const [TagOfFriend, setTagOfFriend] = useState<string>(); // 好友所在分组

    // 获取用户所在的分组
    // !!!!!可能会有问题
    useEffect(() => {
        if (!open) { // 只在打开好友抽屉时获取
            return;
        }
        const fetchTag = async () => {
            console.log("开始获取好友的标签");
            try {
                const params = {
                    member_user_id: String(FriendsProfile?.id),
                };
                const queryString = new URLSearchParams(params).toString();
                const urlforsearch = `${BACKEND_URL}/api/friends/get/position?${queryString}`;
                const response = await fetch(urlforsearch, {
                    method: "GET",
                    headers: {
                        Authorization: `${store.getState().auth.token}`,
                    },
                });
                const bodys = await response.json();

                if (bodys.code === 0) {
                    console.log("成功获取到好友的标签:", bodys.group);
                    setTagOfFriend(bodys.group);
                }
                else {
                    console.error("获取好友的标签失败");
                }
            }
            catch (err) {
                console.error("获取好友的标签时发生错误:", err);
            }
        };
        fetchTag();
    }, [FriendsProfile]);

    // 获取标签列表
    useEffect(() => {
        if (childrenDrawer) { // 只在关闭标签抽屉时获取
            return;
        }
        const fetchTags = async () => {
            console.log("开始获取biaoqian列表");
            try {
                const response = await fetch(`${BACKEND_URL}/api/friends/friends/groups`, {
                    method: "GET",
                    headers: {
                        Authorization: `${store.getState().auth.token}`,
                    },
                });

                const bodys = await response.json();

                if (bodys.code === 0) {
                    const tagList: string[] = [];
                    for (const body of bodys.groups) {
                        // console.log(body);
                        const mytag: string = body.name;
                        tagList.push(mytag);
                    }
                    setTags([...tagList]); //后期改成请求
                    console.log("成功获取到biaoqian列表");
                }
                else {
                    console.error("biaoqian列表获取失败:");
                }
            }
            catch (err) {
                console.error("获取biaoqian列表时发生错误:", err);
            }
        };
        fetchTags();
    }, [childrenDrawer]);

    useEffect(() => {
        if (inputVisible) {
            inputRef.current?.focus();
        }
    }, [inputVisible]);

    useEffect(() => {
        editInputRef.current?.focus();
    }, [editInputValue]);

    const handleClose = async (removedTag: string) => {
        const newTags = tags.filter((tag) => tag !== removedTag);
        console.log(newTags);
        setTags(newTags);
        if (TagOfFriend === removedTag) { // 如果正好删除了该好友所在的标签
            setTagOfFriend(tags[0]);
        }

        await fetch(`${BACKEND_URL}/api/friends/remove/group`, {
            method: "DELETE",
            headers: {
                Authorization: `${store.getState().auth.token}`,
            },
            body: JSON.stringify({
                group_name: removedTag,
            }),
        })
            .then((res) => res.json())
            .then((res) => {
                if (Number(res.code) === 0) {
                    console.log("成功删除标签:" + removedTag);
                    message.success("成功删除标签:" + removedTag);
                }
                else {
                    message.error(res.code + " " + res.info);
                }
            })
            .catch((err) => message.error("标签添加错误：" + err));
    };

    const addNewTag = async () => { // 新标签请求
        await fetch(`${BACKEND_URL}/api/friends/friend/group/create`, {
            method: "POST",
            headers: {
                Authorization: `${store.getState().auth.token}`,
            },
            body: JSON.stringify({
                group_name: inputValue,
            }),
        })
            .then((res) => res.json())
            .then((res) => {
                if (Number(res.code) === 0) {
                    console.log("成功添加标签:" + inputValue);
                    message.success("成功添加标签:" + inputValue);
                }
                else {
                    alert(res.code + " " + res.info);
                }
            })
            .catch((err) => alert("标签添加错误：" + err));
    };

    const EditOldTag = async (oldTag: string) => { // 编辑旧标签请求
        await fetch(`${BACKEND_URL}/api/friends/rename/group`, {
            method: "PUT",
            headers: {
                Authorization: `${store.getState().auth.token}`,
            },
            body: JSON.stringify({
                old_name: oldTag,
                new_name: editInputValue,
            }),
        })
            .then((res) => res.json())
            .then((res) => {
                if (Number(res.code) === 0) {
                    console.log("成功更改标签:" + oldTag + "->" + editInputValue);
                    message.success("成功更改标签:" + oldTag + "->" + editInputValue);
                }
                else {
                    message.error(res.code + " " + res.info);
                }
            })
            .catch((err) => message.error("标签更改错误：" + err));
    };


    // 新建标签时调用
    const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setInputValue(e.target.value);
    };

    const handleInputConfirm = () => {
        if (inputValue && !tags.includes(inputValue)) {
            setTags([...tags, inputValue]);
            addNewTag();
        }
        setInputVisible(false);
        setInputValue("");
    };

    // 编辑旧标签时调用
    const handleEditInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setEditInputValue(e.target.value);
    };

    const handleEditInputConfirm = () => {
        const newTags = [...tags];
        const oldTag = tags[editInputIndex];
        newTags[editInputIndex] = editInputValue;
        setTags(newTags);
        if (oldTag !== editInputValue) {
            EditOldTag(oldTag); // 编辑旧标签请求
        }
        setEditInputIndex(-1);
        setEditInputValue("");
    };

    // 移动到另一个分组
    const handleMove = async (tag: string) => {
        if (tag === TagOfFriend) {
            return;
        }
        await fetch(`${BACKEND_URL}/api/friends/friend/group/move`, {
            method: "POST",
            headers: {
                Authorization: `${store.getState().auth.token}`,
            },
            body: JSON.stringify({
                user_id: String(FriendsProfile?.id),
                group_name: tag,
            }),
        })
            .then((res) => res.json())
            .then((res) => {
                if (Number(res.code) === 0) {
                    console.log("成功移动好友:" + TagOfFriend + "->" + tag);
                    setTagOfFriend(tag);
                }
                else {
                    message.error(res.code + " " + res.info);
                }
            })
            .catch((err) => message.error("标签更改错误：" + err));
    };
    const createGroupChat = async (groupName: string, selectedFriends: number[]) => {
        console.log(groupName);
        console.log(selectedFriends);
        await fetch(`${BACKEND_URL}/api/group/create`, {
            method: "POST",
            headers: {
                Authorization: `${store.getState().auth.token}`,
            },
            body: JSON.stringify({
                members: selectedFriends,
                name: groupName
            }),
        })
            .then((res) => res.json())
            .then((res) => {
                console.log(res);
                console.log(selectedFriends);
                if (Number(res.code) === 0) {
                    message.success("成功创建群聊");
                }
                else {
                    message.error(res.code + " " + res.info);
                }
            })
            .catch((err) => message.error("标签更改错误：" + err));
    };
    const tagPlusStyle: React.CSSProperties = {
        height: 22,
        background: token.colorBgContainer,
        borderStyle: "dashed",
    };


    /* 分组信息 */
    const [sortListOpen, setSortListOpen] = useState(false);
    const [sortList, setSortList] = useState<FriendsDataType[]>([]);
    const [searchUserGroupName, setSearchUserGroupName] = useState<string>("");
    const [usersByGroup, setUsersByGroup] = useState<FriendsDataType[]>([]);

    const searchUsersByGroup = async () => {
        console.log("searchUserGroupName:", searchUserGroupName);
        // const params = {
        //     group_name: searchUserGroupName,
        // };
        // const queryString = new URLSearchParams(params).toString();
        const urlforsearch = `${BACKEND_URL}/api/friends/get/all/ingroup?group_name=${searchUserGroupName}`;
        const response = await fetch(urlforsearch, {
            method: "GET",
            headers: {
                Authorization: `${store.getState().auth.token}`,
            },
        });
        const bodys = await response.json();

        if (bodys.code === 0) {
            const userList = bodys.members;
            const myUserList: FriendsDataType[] = [];
            for (const user of userList) {
                const myUser: FriendsDataType = {
                    name: user.name,
                    avatar: user.avatar,
                    id: user.id,
                    status: 0,
                    sendStatus: "",
                };
                myUserList.push(myUser);
            }
            setUsersByGroup([...myUserList]);
            console.log("成功获取到分组内的用户列表");
        }
        else {
            console.error("获取好友分组失败");
        }
    };

    return (
        <Layout style={{ minHeight: "95vh" }}>
            <SiderBar defaultKey={"4"} handleItemClick={handleItemClick} >
                <div className="demo-logo-vertical" />
            </SiderBar>
            <Sider style={{ overflow: "auto", backgroundColor: "lightgrey" }}>
                <div className="list-vertical" />
                <List
                    dataSource={myFriends}
                    renderItem={(item) => (
                        <List.Item
                            key={item.id}
                            style={item.id === FriendsProfile?.id ? { backgroundColor: "grey" } : { backgroundColor: "lightgrey" }}
                            onClick={() => {
                                setFriendsProfile(item);
                                setOpen(true);
                            }} >
                            <Badge size="default">
                                <Avatar shape="square" size="large" src={item.avatar} />
                            </Badge>
                            <List.Item.Meta
                                title={item.name}
                                style={{ marginLeft: "10px" }}
                            />
                        </List.Item>
                    )}
                />
            </Sider>
            <Drawer width={640} placement="right" closable={false} onClose={() => { setOpen(false); }} open={open}>
                <p className="site-description-item-profile-p" style={{ marginBottom: 24 }}>
                    User Profile
                </p>
                <Avatar src={FriendsProfile?.avatar} size={64} />
                <Divider />
                <Row>
                    <Col span={12}>
                        <DescriptionItem title="Name" content={FriendsProfile?.name} />
                    </Col>
                </Row>
                <Divider />
                <Button
                    type="primary"
                    danger
                    key={"delete-btn"}
                    onClick={() => {
                        deleteFriend();
                    }}>
                    Delete Friend
                </Button>
                <Button
                    key={"tag-btn"}
                    onClick={() => { setChildrenDrawer(true); }}
                >
                    Tags
                </Button >
                <Drawer
                    title="Tags"
                    width={320}
                    closable={false}
                    onClose={() => { setChildrenDrawer(false); }}
                    open={childrenDrawer}
                >
                    <Col span={12}>
                        <DescriptionItem title="The user belongs to" content={TagOfFriend} />
                    </Col>
                    <Divider />
                    <Flex gap="4px 0" >
                        {tags.map<React.ReactNode>((tag, index) => {
                            if (editInputIndex === index) {
                                return (
                                    <Input
                                        ref={editInputRef}
                                        key={tag}
                                        size="small"
                                        style={tagInputStyle}
                                        value={editInputValue}
                                        onChange={handleEditInputChange}
                                        onBlur={handleEditInputConfirm}
                                        onPressEnter={handleEditInputConfirm}
                                    />
                                );
                            }
                            const isLongTag = tag.length > 20;
                            const tagElem = (
                                <Tag
                                    key={tag}
                                    closable={index !== 0}
                                    style={{ userSelect: "none" }}
                                    onClose={() => handleClose(tag)}
                                    onClick={() => handleMove(tag)}
                                >
                                    <span
                                        onDoubleClick={(e) => {
                                            if (index !== 0) {
                                                setEditInputIndex(index); // 发现一个问题，双击标签必然先触发单击lollll
                                                setEditInputValue(tag);
                                                e.preventDefault();
                                            }
                                        }}
                                    >
                                        {isLongTag ? `${tag.slice(0, 20)}...` : tag}
                                    </span>
                                </Tag>
                            );
                            return isLongTag ? (
                                <Tooltip title={tag} key={tag}>
                                    {tagElem}
                                </Tooltip>
                            ) : (
                                tagElem
                            );
                        })};
                        {inputVisible ? (
                            <Input
                                ref={inputRef}
                                type="text"
                                size="small"
                                style={tagInputStyle}
                                value={inputValue}
                                onChange={handleInputChange}
                                onBlur={handleInputConfirm}
                                onPressEnter={handleInputConfirm}
                            />
                        ) : (
                            <Tag
                                style={tagPlusStyle}
                                icon={<PlusOutlined />}
                                onClick={() => {
                                    setInputVisible(true);
                                }}>
                                New Tag
                            </Tag>
                        )};
                    </Flex>


                </Drawer>
            </Drawer>

            <Layout>
                <Header style={{ padding: 20, display: "flex", alignItems: "center" }}>
                    <Search
                        placeholder="search users"
                        value={searchUser}
                        onChange={(e) => setSearchUser(e.target.value)}
                        onSearch={searchFriends}
                        style={{ width: 200 }} />
                    <a onClick={() => {
                        setUnackList(true);
                        ToAcceptList;
                    }} style={{ marginLeft: 20 }}>
                        <Badge count={unack.length} size="small">
                            <Avatar shape="square" size="small" src={<UserAddOutlined />} />
                        </Badge>
                    </a>
                    <a onClick={() => {
                        setCreateGroupList(true);
                    }} style={{ marginLeft: 20 }}>
                        <Badge count={0} size="small">
                            <Avatar shape="square" size="small" src={<TeamOutlined />} />
                        </Badge>
                    </a>
                    <a onClick={() => {
                        setSortListOpen(true);
                    }} style={{ marginLeft: 20 }}>
                        <Avatar shape="square" size="small" src={<AppstoreOutlined />} />
                    </a>
                </Header>
                <Drawer width={640} placement="right" closable={false} onClose={() => { setSortListOpen(false); }} open={sortListOpen}>
                    <Select
                        style={{ width: 120 }}
                        onChange={(e) => {
                            setSearchUserGroupName(String(e));
                            console.log("选择的group:", e);
                        }}
                        options={tags.map(tag => ({ label: tag, value: tag }))}
                    />
                    <Button onClick={() => {
                        searchUsersByGroup();
                    }}>搜索分组</Button>
                    <div style={{ height: "400px", overflow: "auto", display: "flex", flexDirection: "column" }}>
                        {usersByGroup.map((item, index) => (
                            <div key={index} style={{ display: "flex", flexDirection: "row" }}>
                                <Avatar src={item.avatar} />
                                <div>{item.name}</div>
                            </div>
                        ))}
                    </div>
                </Drawer>
                <Drawer width={640} placement="right" closable={false} onClose={() => { setUnackList(false); }} open={UnackList}>
                    <List
                        dataSource={unack}
                        renderItem={(item) => {
                            // 检查item.avatar和item.name是否有有效的值
                            if (!item.avatar || !item.name) {
                                console.error("Invalid item:", item);
                            }

                            return (
                                <List.Item
                                    key={item.id}
                                    // style={{ background: "#808080" }}
                                    actions={[
                                        <Button
                                            className={"ack-friend"}
                                            key={"accept-btn"}
                                            onClick={() => {
                                                const itemid: number = item.id;
                                                item.status = 1;
                                                setToAccept(itemid);
                                                setAckRefuse("accept");
                                                // 接受
                                            }}
                                            disabled={(item.status === 1) ? true : false}>
                                            accept
                                        </Button>,
                                        <Button
                                            className={"rufuse-friend"}
                                            key={"refuse-btn"}
                                            onClick={() => {
                                                const itemid: number = item.id;
                                                item.status = 1;
                                                setToAccept(itemid);
                                                setAckRefuse("reject");
                                                // 拒绝
                                            }}
                                            disabled={(item.status === 1) ? true : false}>
                                            reject
                                        </Button>]} >
                                    <List.Item.Meta
                                        avatar={<Avatar src={item.avatar} />}
                                        title={<a>{item.name}</a>}
                                    />
                                </List.Item>
                            );
                        }}
                    />
                </Drawer>
                <Drawer width={640} placement="right" closable={false} onClose={() => { setCreateGroupList(false); }} open={CreateGroupList}>
                    <List
                        dataSource={myFriends.filter(item => item.id !== store.getState().auth.id)}
                        renderItem={(item) => {
                            // 检查item.avatar和item.name是否有有效的值
                            if (!item.name) {
                                console.error("Invalid item:", item);
                            }
                            return (
                                <List.Item>
                                    <Checkbox
                                        checked={selectedFriends.includes(item.id)}
                                        onChange={(e) => {
                                            if (e.target.checked) {
                                                setSelectedFriends([...selectedFriends, item.id]);
                                            }
                                            else {
                                                setSelectedFriends(selectedFriends.filter(id => id !== item.id));
                                            }
                                        }
                                        }
                                    >
                                        {item.name}
                                    </Checkbox>
                                </List.Item>
                            );
                        }}
                    />
                    <Input placeholder="输入群聊名称" value={groupName} onChange={e => setGroupName(e.target.value)} />
                    <Button onClick={() => createGroupChat(groupName, selectedFriends)}>创建群聊</Button>
                </Drawer>

                <Content style={{ margin: "0 16px" }}>
                    <List
                        pagination={{ position, align }}
                        dataSource={userdata}
                        renderItem={(item) => (
                            <List.Item
                                key={item.id}
                                actions={[
                                    <Button
                                        className={"send-request-btn"}
                                        key={item.id}
                                        onClick={async () => {
                                            const itemforprofile: number = item.id;
                                            setUserProfile(itemforprofile);
                                            item.status = 2;
                                            item.sendStatus = "waiting for response";
                                        }}
                                        disabled={(item.status === 0) ? false : true}>
                                        {item.sendStatus}
                                    </Button>]}>
                                <List.Item.Meta
                                    avatar={<Avatar src={item.avatar} />}
                                    title={<a>{item.name}</a>}
                                />
                            </List.Item>
                        )}
                    />
                </Content>

            </Layout>
        </Layout>
    );
};

export default ListPage;