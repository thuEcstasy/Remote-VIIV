import React, { useState } from "react";
import {
    DesktopOutlined,
    FileOutlined,
    PieChartOutlined,
    UserOutlined,
    AlignLeftOutlined,
} from "@ant-design/icons";
import type { MenuProps } from "antd";
import { Breadcrumb, Layout, Menu, theme } from "antd";

const { Header, Content, Footer, Sider } = Layout;

type MenuItem = Required<MenuProps>["items"][number];

function getItem(
    key: React.Key,
    icon?: React.ReactNode,
    children?: MenuItem[],
): MenuItem {
    return {
        key,
        icon,
        children,
    } as MenuItem;
}

const items: MenuItem[] = [
    getItem("1", <PieChartOutlined />),
    getItem("2", <DesktopOutlined />),
    getItem("3", <FileOutlined />,),
    getItem("4", <UserOutlined />,),
    getItem("5", <AlignLeftOutlined />),
];

interface SiderBarProps {
    children: React.ReactNode;
    defaultKey: string;
    handleItemClick: ({ key }: { key: string }) => void;
}

const SiderBar: React.FC<SiderBarProps> = ({ defaultKey, handleItemClick }) => {
    const [collapsed, setCollapsed] = useState(true);
    const {
        token: { colorBgContainer, borderRadiusLG },
    } = theme.useToken();

    return (
        <Sider width={70}>
            <div className="demo-logo-vertical" />
            <Menu
                onClick={handleItemClick}
                theme="dark"
                defaultSelectedKeys={[defaultKey]}
                mode="inline"
                items={items}
            />
        </Sider>
    );
};

export default SiderBar;