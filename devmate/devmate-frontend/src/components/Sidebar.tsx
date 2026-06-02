import React from "react";

type Conversation = {
  id: number;
  title: string;
};

type Props = {
  conversations: Conversation[];
  currentId: number | null;
  onSelect: (id: number) => void;
  onNewChat: () => void;
};

export default function Sidebar({
  conversations,
  currentId,
  onSelect,
  onNewChat,
}: Props) {
  return (
    <div style={styles.sidebar}>
      <div style={styles.header}>
        <h2>DevMate</h2>

        <button style={styles.newBtn} onClick={onNewChat}>
          + New Chat
        </button>
      </div>

      <div style={styles.list}>
        {conversations.map((chat) => (
          <div
            key={chat.id}
            onClick={() => onSelect(chat.id)}
            style={{
              ...styles.item,
              background:
                currentId === chat.id ? "#2c2c2c" : "transparent",
            }}
          >
            💬 {chat.title || `Chat ${chat.id}`}
          </div>
        ))}
      </div>
    </div>
  );
}

const styles: any = {
  sidebar: {
    width: "260px",
    height: "100vh",
    backgroundColor: "#1e1e1e",
    color: "white",
    padding: "10px",
    display: "flex",
    flexDirection: "column",
  },
  header: {
    display: "flex",
    flexDirection: "column",
    gap: "10px",
    marginBottom: "10px",
  },
  newBtn: {
    padding: "8px",
    background: "#3b82f6",
    border: "none",
    color: "white",
    cursor: "pointer",
    borderRadius: "6px",
  },
  list: {
    display: "flex",
    flexDirection: "column",
    gap: "5px",
    overflowY: "auto",
  },
  item: {
    padding: "8px",
    cursor: "pointer",
    borderRadius: "6px",
  },
};
