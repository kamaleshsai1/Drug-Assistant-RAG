import React from "react";
import Message from "./Message";

function ChatWindow({
  messages = [],
  loading = false,
  onOpenSource
}) {
  return (
    <div className="chat-window">
      <div className="messages">
        {messages.map((message, index) => (
          <Message
            key={
              message?.id ||
              `message-${index}`
            }
            message={message}
            onOpenSource={onOpenSource}
          />
        ))}

        {loading && (
          <div className="message-row assistant-row">
            <div className="message-avatar assistant-avatar">
              <span>✚</span>
            </div>

            <div className="message-bubble assistant-bubble">
              <div className="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default ChatWindow;