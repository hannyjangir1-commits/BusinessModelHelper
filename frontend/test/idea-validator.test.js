import test from 'node:test';
import assert from 'node:assert/strict';
import React from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { safeText, normalizeValidationReportData } from '../src/utils/validator.ts';

/**
 * Functional component representation of the fixed ValidationQuestionCard
 * using standard React.createElement (matching IdeaValidatorView.tsx).
 */
function ValidationQuestionCardComponent({ question, index }) {
  const isObj = typeof question === 'object' && question !== null;
  const questionText = isObj
    ? question.question_text || question.question || question.text || ''
    : String(question || '');
  const focusCategory = isObj
    ? question.focus_category || question.category || question.focus
    : undefined;
  const rationale = isObj
    ? question.rationale || question.reasoning || question.why
    : undefined;

  return React.createElement(
    'div',
    { className: 'p-3.5 rounded-xl bg-slate-50 border' },
    React.createElement(
      'div',
      { className: 'flex items-start justify-between gap-3' },
      React.createElement(
        'div',
        { className: 'flex items-start gap-2.5' },
        React.createElement('span', { className: 'index-badge' }, index + 1),
        React.createElement('p', { className: 'question-text' }, questionText || 'Unspecified validation inquiry')
      ),
      focusCategory ? React.createElement('span', { className: 'category-badge' }, focusCategory) : null
    ),
    rationale ? React.createElement('p', { className: 'rationale-text' }, rationale) : null
  );
}

/**
 * Functional component representation of the fixed ValidationExperimentCard.
 */
function ValidationExperimentCardComponent({ experiment, index }) {
  return React.createElement(
    'div',
    { className: 'border rounded-xl p-3.5' },
    React.createElement('h4', null, safeText(experiment.experiment_name, 'Validation Experiment')),
    React.createElement('span', null, safeText(experiment.experiment_type)),
    React.createElement('p', null, safeText(experiment.hypothesis)),
    React.createElement('span', null, safeText(experiment.success_criteria))
  );
}

test('REGRESSION REPRODUCTION: Passing an un-normalized question object directly as a React child throws React Error #31', () => {
  const rawQuestionObject = {
    question_text: 'How do you currently validate client demand before building an MVP?',
    focus_category: 'Past Behavior',
    rationale: 'Exposes actual user habits rather than polite speculation.',
  };

  // This was the original offending expression in IdeaValidatorView:
  // <li key={idx}>{q}</li> where q was rawQuestionObject
  assert.throws(
    () => {
      renderToStaticMarkup(React.createElement('li', null, rawQuestionObject));
    },
    (err) => {
      assert(err instanceof Error);
      assert(err.message.includes('Objects are not valid as a React child'));
      assert(err.message.includes('question_text'));
      assert(err.message.includes('focus_category'));
      return true;
    }
  );
});

test('1. Validation question represented as an object with question_text and focus_category is safely rendered', () => {
  const structuredQuestion = {
    question_text: 'What was the last tool you paid for to solve this problem?',
    focus_category: 'Budget Authority',
    rationale: 'Verifies actual willingness to pay.',
  };

  const html = renderToStaticMarkup(
    React.createElement(ValidationQuestionCardComponent, { question: structuredQuestion, index: 0 })
  );

  assert(typeof html === 'string');
  assert(html.includes('What was the last tool you paid for to solve this problem?'));
  assert(html.includes('Budget Authority'));
  assert(html.includes('Verifies actual willingness to pay.'));
});

test('2. Arrays of validation questions (objects, strings, alternate aliases) and experiments', () => {
  const rawData = {
    interview_questions: [
      { question_text: 'Question 1', focus_category: 'Past Behavior', rationale: 'Reason 1' },
      { question: 'Alternative Key Question', category: 'Current Friction' },
      'Plain string question without object wrapper',
      null,
    ],
    validation_experiments: [
      {
        experiment_name: 'Smoke Test',
        experiment_type: 'Landing Page',
        hypothesis: 'Conversion rate >= 5%',
        target_audience: 'Founders',
        procedure: 'Deploy landing page with waitlist',
        estimated_duration: '1 week',
        estimated_cost: '$20',
        success_criteria: '50 signups',
      },
    ],
  };

  const normalized = normalizeValidationReportData(rawData);
  assert(normalized !== null);
  assert.equal(normalized.interview_questions.length, 4);

  // First question
  assert.equal(normalized.interview_questions[0].question_text, 'Question 1');
  assert.equal(normalized.interview_questions[0].focus_category, 'Past Behavior');

  // Second question with aliases
  assert.equal(normalized.interview_questions[1].question_text, 'Alternative Key Question');
  assert.equal(normalized.interview_questions[1].focus_category, 'Current Friction');

  // Third question plain string
  assert.equal(normalized.interview_questions[2].question_text, 'Plain string question without object wrapper');
  assert.equal(normalized.interview_questions[2].focus_category, 'General');

  // Fourth question null fallback
  assert.equal(normalized.interview_questions[3].question_text, '');

  // Render all questions and experiments through components without crashing
  const renderedQuestions = normalized.interview_questions.map((q, i) =>
    renderToStaticMarkup(React.createElement(ValidationQuestionCardComponent, { key: i, question: q, index: i }))
  );
  assert.equal(renderedQuestions.length, 4);
  assert(renderedQuestions[0].includes('Question 1'));
  assert(renderedQuestions[1].includes('Alternative Key Question'));
  assert(renderedQuestions[2].includes('Plain string question without object wrapper'));

  const renderedExperiment = renderToStaticMarkup(
    React.createElement(ValidationExperimentCardComponent, { experiment: normalized.validation_experiments[0], index: 0 })
  );
  assert(renderedExperiment.includes('Smoke Test'));
  assert(renderedExperiment.includes('Conversion rate &gt;= 5%'));
});

test('3. Optional or missing fields handled gracefully without exceptions', () => {
  const minimalData = {};
  const normalized = normalizeValidationReportData(minimalData);
  assert(normalized !== null);
  assert.deepEqual(normalized.interview_questions, []);

  // safeText on null, undefined, empty
  assert.equal(safeText(null), '');
  assert.equal(safeText(undefined, 'fallback'), 'fallback');
  assert.equal(safeText(''), '');

  // Render question card with empty values
  const emptyHtml = renderToStaticMarkup(
    React.createElement(ValidationQuestionCardComponent, { question: '', index: 0 })
  );
  assert(emptyHtml.includes('Unspecified validation inquiry'));
});

test('4. Complete report containing SWOT, risks, experiments, customer clarity, and questions', () => {
  const completeReport = {
    overview: 'High venture viability with critical customer acquisition risks.',
    problem_solution_fit: {
      problem_statement: 'Invoicing manual errors consume 5 hours weekly for contractors.',
      who_experiences_it: 'Freelancers & micro-agencies',
      frequency_and_severity: 'Weekly high-friction billing cycle',
      existing_alternatives: ['Spreadsheets', 'Manual Word templates'],
    },
    target_customer_clarity: {
      primary_segment: 'Solo technical consultants',
      buyer_vs_end_user: 'Same person (founder/solo operator)',
      adoption_barriers: ['Hesitation to switch payment providers'],
      unvalidated_assumptions: ['Willingness to pay $19/month'],
    },
    swot_analysis: {
      strengths: ['Deterministic math', 'Fast setup'],
      weaknesses: ['No mobile app initially'],
      opportunities: ['Growing gig economy in Europe'],
      threats: ['Incumbent feature copycats'],
    },
    business_risks: [
      {
        category: 'Market',
        description: 'Payment processors increase fee rates',
        likelihood: 'Medium',
        impact: 'High',
        suggested_mitigation: 'Multi-gateway redundancy',
        recommended_next_action: 'Integrate Stripe and Paddle',
      },
    ],
    validation_experiments: [
      {
        experiment_name: 'Consultant Discovery Calls',
        experiment_type: 'Customer Interviews',
        hypothesis: '8 of 10 consultants report billing stress',
        success_criteria: '80% validation rate',
      },
    ],
    interview_questions: [
      {
        question_text: 'When was the last time a client disputed your invoice?',
        focus_category: 'Past Behavior',
        rationale: 'Identifies actual pain severity rather than polite agreement.',
      },
      {
        question_text: 'What is your current manual invoicing process costing you in hours?',
        focus_category: 'Current Friction',
        rationale: 'Quantifies economic value of the problem.',
      },
    ],
    summary: {
      qualitative_readiness_assessment: 'Pre-Validation (Discovery)',
      strongest_supporting_evidence: 'High willingness to pay observed in initial founder tests',
    },
  };

  const normalized = normalizeValidationReportData(completeReport);
  assert(normalized !== null);

  // Validate that safeText safely formats all array elements
  const strengthStrings = normalized.swot_analysis.strengths.map((s) => safeText(s));
  assert.equal(strengthStrings[0], 'Deterministic math');

  const riskCat = safeText(normalized.business_risks[0].category);
  assert.equal(riskCat, 'Market');

  // Render question cards
  const qHtml = normalized.interview_questions
    .map((q, i) => renderToStaticMarkup(React.createElement(ValidationQuestionCardComponent, { question: q, index: i })))
    .join('');
  assert(qHtml.includes('When was the last time a client disputed your invoice?'));
  assert(qHtml.includes('Past Behavior'));
  assert(qHtml.includes('Current Friction'));
});

test('5. Unexpected field types (numbers, booleans, nested unexpected objects)', () => {
  // safeText handles numbers, booleans, nested objects safely without returning an object
  assert.equal(safeText(42), '42');
  assert.equal(safeText(true), 'true');
  assert.equal(safeText(false), 'false');
  assert.equal(safeText({ title: 'Object with title' }), 'Object with title');
  assert.equal(safeText({ description: 'Object with description' }), 'Object with description');
  assert.equal(safeText({ custom_key: 'custom_val' }), '{"custom_key":"custom_val"}');

  // Normalizer handles weird question inputs
  const weirdQuestions = [
    12345,
    true,
    { weird_field: 'Some text' },
  ];
  const normalized = normalizeValidationReportData({ interview_questions: weirdQuestions });
  assert.equal(normalized.interview_questions.length, 3);
  assert.equal(normalized.interview_questions[0].question_text, '12345');
  assert.equal(normalized.interview_questions[1].question_text, 'true');

  // Render through component safely
  for (let i = 0; i < normalized.interview_questions.length; i++) {
    const html = renderToStaticMarkup(
      React.createElement(ValidationQuestionCardComponent, { question: normalized.interview_questions[i], index: i })
    );
    assert(typeof html === 'string');
    assert(html.length > 0);
  }
});

test('6. Valid report renders cleanly without any React exceptions', () => {
  const reportData = {
    overview: 'Clean Executive Evaluation',
    interview_questions: [
      {
        question_text: 'How do you currently track business expenses?',
        focus_category: 'Existing Workaround',
        rationale: 'Identifies competitor penetration and manual friction.',
      },
    ],
    validation_experiments: [
      {
        experiment_name: 'Prototype Demo',
        experiment_type: 'Prototype',
        hypothesis: 'Founders can finish model setup in under 5 minutes',
        estimated_duration: '2 days',
        success_criteria: '5/5 complete without assistance',
      },
    ],
  };

  const normalized = normalizeValidationReportData(reportData);
  assert(normalized !== null);

  const qHtml = renderToStaticMarkup(
    React.createElement(ValidationQuestionCardComponent, { question: normalized.interview_questions[0], index: 0 })
  );
  assert(qHtml.includes('How do you currently track business expenses?'));
  assert(qHtml.includes('Existing Workaround'));

  const expHtml = renderToStaticMarkup(
    React.createElement(ValidationExperimentCardComponent, { experiment: normalized.validation_experiments[0], index: 0 })
  );
  assert(expHtml.includes('Prototype Demo'));
  assert(expHtml.includes('Founders can finish model setup in under 5 minutes'));
});
