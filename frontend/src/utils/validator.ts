import type { CustomerInterviewQuestion, InterviewQuestionItem, ValidationReportData } from '../types';

/**
 * Safely extracts a displayable string from any scalar or object.
 * Prevents raw objects from ever being passed directly as React children.
 */
export function safeText(val: any, fallback: string = ''): string {
  if (val === null || val === undefined) return fallback;
  if (typeof val === 'string') return val;
  if (typeof val === 'number' || typeof val === 'boolean') return String(val);
  if (typeof val === 'object') {
    return (
      val.question_text ||
      val.question ||
      val.text ||
      val.description ||
      val.title ||
      val.name ||
      JSON.stringify(val)
    );
  }
  return String(val);
}

/**
 * Extracts the primary question text safely from any question item shape.
 */
export function getQuestionText(question: any): string {
  if (typeof question === 'string') return question;
  if (typeof question === 'object' && question !== null) {
    return (
      question.question_text ||
      question.question ||
      question.text ||
      question.title ||
      question.description ||
      (Object.keys(question).length > 0 ? JSON.stringify(question) : '')
    );
  }
  return String(question || '');
}

/**
 * Extracts the focus category from a question item or raw object.
 */
export function getQuestionFocusCategory(question: any): string | undefined {
  if (typeof question === 'object' && question !== null) {
    return question.focus_category || question.category || question.focus;
  }
  return undefined;
}

/**
 * Extracts the rationale from a question item or raw object.
 */
export function getQuestionRationale(question: any): string | undefined {
  if (typeof question === 'object' && question !== null) {
    return question.rationale || question.reasoning || question.why;
  }
  return undefined;
}


/**
 * Normalizes ValidationReportData so that all fields, especially interview_questions,
 * conform to structured expectations regardless of backend variations.
 */
export function normalizeValidationReportData(data: any): ValidationReportData | null {
  if (!data || typeof data !== 'object') return null;

  const rawQuestions = Array.isArray(data.interview_questions) ? data.interview_questions : [];
  const normalizedQuestions: InterviewQuestionItem[] = rawQuestions.map((q: any) => {
    if (q === null || q === undefined) {
      return { question_text: '', focus_category: 'General' } as CustomerInterviewQuestion;
    }
    if (typeof q === 'string' || typeof q === 'number' || typeof q === 'boolean') {
      return { question_text: String(q), focus_category: 'General' } as CustomerInterviewQuestion;
    }
    if (typeof q === 'object') {
      const qText =
        q.question_text ||
        q.question ||
        q.text ||
        q.title ||
        q.description ||
        (Object.keys(q).length > 0 ? JSON.stringify(q) : '');
      return {
        question_text: String(qText || ''),
        focus_category: String(q.focus_category || q.category || q.focus || 'General'),
        rationale: q.rationale ? String(q.rationale) : undefined,
      } as CustomerInterviewQuestion;
    }
    return { question_text: String(q), focus_category: 'General' } as CustomerInterviewQuestion;
  });

  return {
    ...data,
    interview_questions: normalizedQuestions,
  };
}
