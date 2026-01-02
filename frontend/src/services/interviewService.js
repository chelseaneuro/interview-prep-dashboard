import axios from 'axios';

class InterviewService {
  constructor() {
    this.baseURL = 'http://localhost:5000';
  }

  async generateResponse(question, profile, jobId = null) {
    try {
      const response = await axios.post(`${this.baseURL}/api/interview/generate`, {
        question,
        profile,
        job_id: jobId
      });
      return response.data;
    } catch (error) {
      console.error('Error generating interview response:', error);
      throw error;
    }
  }
}

export default new InterviewService();
