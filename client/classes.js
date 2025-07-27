import router from "./router.js";

class Note {
  constructor(note) {
    this.title = note?.title;
    this.lastModified = note?.lastModified;
    this.content = note?.content;
  }

  get lastModifiedAsDate() {
    return new Date(this.lastModified * 1000);
  }

  get lastModifiedAsString() {
    return this.lastModifiedAsDate.toLocaleString();
  }
}

class SearchResult extends Note {
  constructor(searchResult) {
    super(searchResult);
    this.score = searchResult.score;
    this.titleHighlights = searchResult.titleHighlights;
    this.contentHighlights = searchResult.contentHighlights;
    this.tagMatches = searchResult.tagMatches;
  }

  get titleHighlightsOrTitle() {
    return this.titleHighlights ? this.titleHighlights : this.title;
  }

  get includesHighlights() {
    if (
      this.titleHighlights ||
      this.contentHighlights ||
      (this.tagMatches != null && this.tagMatches.length)
    ) {
      return true;
    } else {
      return false;
    }
  }
}

// 聊天消息
class ChatMessage {
  constructor({ sender, content, timestamp }) {
    this.content = content;
    this.sender = sender; // 'user'/'bot'
    this.timestamp = timestamp || Date.now();
  }
}

// 任务信息
// class TaskInfo {
//   constructor({ task_id, user_id, task_type }) {
//     this.task_id = task_id;
//     this.user_id = user_id;
//     this.task_type = task_type || 1;
//   }
// }

class TaskInfo {
  constructor({ query, simple_chat, chat_with_notes, chat_with_knowledge, chat_with_web }) {
    this.query = query;
    this.simple_chat = simple_chat;
    this.chat_with_notes = chat_with_notes;
    this.chat_with_knowledge = chat_with_knowledge;
    this.chat_with_web = chat_with_web;
  }
}

class TaskResult {
  constructor({ task_id, user_id, status, result }){
    this.task_id = task_id;
    this.user_id = user_id;
    this.status = status;
    this.result = result;
  }
}

export { Note, SearchResult, ChatMessage, TaskInfo, TaskResult };
