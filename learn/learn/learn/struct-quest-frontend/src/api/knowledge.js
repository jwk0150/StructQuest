import { http } from '../utils/request'

export const knowledgeApi = {
  getMap() { return http.get('/knowledge/map') },
  getDocs() { return http.get('/knowledge-docs') },
  getStats() { return http.get('/knowledge-stats') },
  getProgress() { return http.get('/knowledge/progress') },
  uploadPdf(file) {
    const formData = new FormData()
    formData.append('file', file)
    return http.post('/upload-pdf', formData, { headers: { 'Content-Type': 'multipart/form-data' } })
  },
  deleteDoc(docId) { return http.delete('/knowledge-docs/' + docId) },
  startNode(nodeId) { return http.post('/nodes/' + nodeId + '/start') },
}
export default knowledgeApi
