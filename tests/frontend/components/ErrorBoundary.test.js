/**
 * 🛡️ Tests unitaires critiques pour ErrorBoundary
 * Tests pour la gestion d'erreurs React, récupération, logging, interfaces de fallback
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import ErrorBoundary from '../../../ui/src/components/ErrorBoundary';

// Mock console.error pour capturer les erreurs
const originalConsoleError = console.error;
beforeAll(() => {
  console.error = jest.fn();
});

afterAll(() => {
  console.error = originalConsoleError;
});

// Composant qui déclenche une erreur pour les tests
const ThrowError = ({ shouldThrow = false, errorMessage = 'Test error', errorType = 'Error' }) => {
  if (shouldThrow) {
    const ErrorClass = errorType === 'TypeError' ? TypeError : Error;
    throw new ErrorClass(errorMessage);
  }
  return <div data-testid="no-error">Component rendered successfully</div>;
};

// Composant qui déclenche une erreur asynchrone
const AsyncError = ({ shouldThrow = false }) => {
  React.useEffect(() => {
    if (shouldThrow) {
      setTimeout(() => {
        throw new Error('Async error');
      }, 100);
    }
  }, [shouldThrow]);
  
  return <div data-testid="async-component">Async component</div>;
};

// Mock des services externes
const mockErrorLogger = {
  logError: jest.fn(),
  logUserAction: jest.fn()
};

const mockErrorReporter = {
  reportError: jest.fn(),
  reportRecovery: jest.fn()
};

describe('ErrorBoundary', () => {
  const defaultProps = {
    fallback: null,
    onError: jest.fn(),
    enableRecovery: true,
    maxRetries: 3,
    errorLogger: mockErrorLogger,
    errorReporter: mockErrorReporter
  };

  beforeEach(() => {
    jest.clearAllMocks();
    console.error.mockClear();
  });

  describe('Rendu normal', () => {
    test('affiche les enfants quand il n\'y a pas d\'erreur', () => {
      render(
        <ErrorBoundary {...defaultProps}>
          <ThrowError shouldThrow={false} />
        </ErrorBoundary>
      );

      expect(screen.getByTestId('no-error')).toBeInTheDocument();
      expect(screen.getByText('Component rendered successfully')).toBeInTheDocument();
    });

    test('fonctionne avec plusieurs enfants', () => {
      render(
        <ErrorBoundary {...defaultProps}>
          <div data-testid="child1">Child 1</div>
          <div data-testid="child2">Child 2</div>
          <ThrowError shouldThrow={false} />
        </ErrorBoundary>
      );

      expect(screen.getByTestId('child1')).toBeInTheDocument();
      expect(screen.getByTestId('child2')).toBeInTheDocument();
      expect(screen.getByTestId('no-error')).toBeInTheDocument();
    });

    test('passe les props aux enfants correctement', () => {
      const TestChild = ({ testProp }) => (
        <div data-testid="test-child">{testProp}</div>
      );

      render(
        <ErrorBoundary {...defaultProps}>
          <TestChild testProp="test value" />
        </ErrorBoundary>
      );

      expect(screen.getByText('test value')).toBeInTheDocument();
    });
  });

  describe('Capture d\'erreurs', () => {
    test('capture les erreurs JavaScript standard', () => {
      render(
        <ErrorBoundary {...defaultProps}>
          <ThrowError shouldThrow={true} errorMessage="Standard error" />
        </ErrorBoundary>
      );

      expect(screen.getByTestId('error-boundary-fallback')).toBeInTheDocument();
      expect(screen.getByText(/something went wrong/i)).toBeInTheDocument();
      expect(screen.getByText(/standard error/i)).toBeInTheDocument();
    });

    test('capture les TypeError', () => {
      render(
        <ErrorBoundary {...defaultProps}>
          <ThrowError shouldThrow={true} errorMessage="Type error" errorType="TypeError" />
        </ErrorBoundary>
      );

      expect(screen.getByTestId('error-boundary-fallback')).toBeInTheDocument();
      expect(screen.getByText(/type error/i)).toBeInTheDocument();
    });

    test('capture les erreurs dans les composants profonds', () => {
      const DeepChild = () => <ThrowError shouldThrow={true} errorMessage="Deep error" />;
      const MiddleChild = () => <DeepChild />;

      render(
        <ErrorBoundary {...defaultProps}>
          <MiddleChild />
        </ErrorBoundary>
      );

      expect(screen.getByTestId('error-boundary-fallback')).toBeInTheDocument();
      expect(screen.getByText(/deep error/i)).toBeInTheDocument();
    });

    test('capture les erreurs lors du rendu initial', () => {
      render(
        <ErrorBoundary {...defaultProps}>
          <ThrowError shouldThrow={true} errorMessage="Initial render error" />
        </ErrorBoundary>
      );

      expect(screen.getByTestId('error-boundary-fallback')).toBeInTheDocument();
    });

    test('capture les erreurs lors des mises à jour', () => {
      const { rerender } = render(
        <ErrorBoundary {...defaultProps}>
          <ThrowError shouldThrow={false} />
        </ErrorBoundary>
      );

      expect(screen.getByTestId('no-error')).toBeInTheDocument();

      rerender(
        <ErrorBoundary {...defaultProps}>
          <ThrowError shouldThrow={true} errorMessage="Update error" />
        </ErrorBoundary>
      );

      expect(screen.getByTestId('error-boundary-fallback')).toBeInTheDocument();
      expect(screen.getByText(/update error/i)).toBeInTheDocument();
    });
  });

  describe('Interface de fallback', () => {
    test('affiche l\'interface de fallback par défaut', () => {
      render(
        <ErrorBoundary {...defaultProps}>
          <ThrowError shouldThrow={true} errorMessage="Test error" />
        </ErrorBoundary>
      );

      expect(screen.getByTestId('error-boundary-fallback')).toBeInTheDocument();
      expect(screen.getByText(/something went wrong/i)).toBeInTheDocument();
      expect(screen.getByText(/test error/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /try again/i })).toBeInTheDocument();
    });

    test('utilise un composant de fallback personnalisé', () => {
      const CustomFallback = ({ error, retry }) => (
        <div data-testid="custom-fallback">
          <h2>Custom Error UI</h2>
          <p>Error: {error.message}</p>
          <button onClick={retry}>Custom Retry</button>
        </div>
      );

      render(
        <ErrorBoundary {...defaultProps} fallback={CustomFallback}>
          <ThrowError shouldThrow={true} errorMessage="Custom error" />
        </ErrorBoundary>
      );

      expect(screen.getByTestId('custom-fallback')).toBeInTheDocument();
      expect(screen.getByText('Custom Error UI')).toBeInTheDocument();
      expect(screen.getByText(/custom error/i)).toBeInTheDocument();
      expect(screen.getByText('Custom Retry')).toBeInTheDocument();
    });

    test('utilise une fonction de fallback', () => {
      const fallbackFunction = (error, retry) => (
        <div data-testid="function-fallback">
          <span>Function Fallback: {error.message}</span>
          <button onClick={retry}>Function Retry</button>
        </div>
      );

      render(
        <ErrorBoundary {...defaultProps} fallback={fallbackFunction}>
          <ThrowError shouldThrow={true} errorMessage="Function error" />
        </ErrorBoundary>
      );

      expect(screen.getByTestId('function-fallback')).toBeInTheDocument();
      expect(screen.getByText(/function error/i)).toBeInTheDocument();
    });

    test('affiche la stack trace en mode développement', () => {
      const originalNodeEnv = process.env.NODE_ENV;
      process.env.NODE_ENV = 'development';

      render(
        <ErrorBoundary {...defaultProps}>
          <ThrowError shouldThrow={true} errorMessage="Dev error" />
        </ErrorBoundary>
      );

      expect(screen.getByTestId('error-stack-trace')).toBeInTheDocument();
      expect(screen.getByText(/stack trace/i)).toBeInTheDocument();

      process.env.NODE_ENV = originalNodeEnv;
    });

    test('cache la stack trace en production', () => {
      const originalNodeEnv = process.env.NODE_ENV;
      process.env.NODE_ENV = 'production';

      render(
        <ErrorBoundary {...defaultProps}>
          <ThrowError shouldThrow={true} errorMessage="Prod error" />
        </ErrorBoundary>
      );

      expect(screen.queryByTestId('error-stack-trace')).not.toBeInTheDocument();

      process.env.NODE_ENV = originalNodeEnv;
    });
  });

  describe('Mécanisme de récupération', () => {
    test('permet la récupération avec le bouton retry', () => {
      const { rerender } = render(
        <ErrorBoundary {...defaultProps} enableRecovery={true}>
          <ThrowError shouldThrow={true} errorMessage="Recoverable error" />
        </ErrorBoundary>
      );

      expect(screen.getByTestId('error-boundary-fallback')).toBeInTheDocument();

      const retryButton = screen.getByRole('button', { name: /try again/i });
      fireEvent.click(retryButton);

      // Simuler que l'erreur est corrigée
      rerender(
        <ErrorBoundary {...defaultProps} enableRecovery={true}>
          <ThrowError shouldThrow={false} />
        </ErrorBoundary>
      );

      expect(screen.getByTestId('no-error')).toBeInTheDocument();
    });

    test('compte les tentatives de récupération', () => {
      render(
        <ErrorBoundary {...defaultProps} maxRetries={2}>
          <ThrowError shouldThrow={true} errorMessage="Retry test" />
        </ErrorBoundary>
      );

      const retryButton = screen.getByRole('button', { name: /try again/i });

      // Première tentative
      fireEvent.click(retryButton);
      expect(screen.getByText(/attempt 1 of 2/i)).toBeInTheDocument();

      // Deuxième tentative
      fireEvent.click(retryButton);
      expect(screen.getByText(/attempt 2 of 2/i)).toBeInTheDocument();

      // Troisième tentative - devrait être désactivée
      fireEvent.click(retryButton);
      expect(retryButton).toBeDisabled();
      expect(screen.getByText(/maximum retry attempts reached/i)).toBeInTheDocument();
    });

    test('désactive la récupération quand configuré', () => {
      render(
        <ErrorBoundary {...defaultProps} enableRecovery={false}>
          <ThrowError shouldThrow={true} errorMessage="No recovery" />
        </ErrorBoundary>
      );

      expect(screen.queryByRole('button', { name: /try again/i })).not.toBeInTheDocument();
      expect(screen.getByText(/recovery disabled/i)).toBeInTheDocument();
    });

    test('réinitialise le compteur de tentatives après récupération réussie', () => {
      const { rerender } = render(
        <ErrorBoundary {...defaultProps} maxRetries={2}>
          <ThrowError shouldThrow={true} errorMessage="Reset test" />
        </ErrorBoundary>
      );

      // Première tentative ratée
      const retryButton = screen.getByRole('button', { name: /try again/i });
      fireEvent.click(retryButton);

      // Récupération réussie
      rerender(
        <ErrorBoundary {...defaultProps} maxRetries={2}>
          <ThrowError shouldThrow={false} />
        </ErrorBoundary>
      );

      expect(screen.getByTestId('no-error')).toBeInTheDocument();

      // Nouvelle erreur - le compteur devrait être réinitialisé
      rerender(
        <ErrorBoundary {...defaultProps} maxRetries={2}>
          <ThrowError shouldThrow={true} errorMessage="New error" />
        </ErrorBoundary>
      );

      // Le compteur devrait être à zéro
      expect(screen.queryByText(/attempt 1 of 2/i)).not.toBeInTheDocument();
    });
  });

  describe('Logging et reporting', () => {
    test('appelle onError lors d\'une erreur', () => {
      const mockOnError = jest.fn();

      render(
        <ErrorBoundary {...defaultProps} onError={mockOnError}>
          <ThrowError shouldThrow={true} errorMessage="Callback error" />
        </ErrorBoundary>
      );

      expect(mockOnError).toHaveBeenCalledWith(
        expect.objectContaining({ message: 'Callback error' }),
        expect.objectContaining({ componentStack: expect.any(String) })
      );
    });

    test('utilise le logger d\'erreurs', () => {
      render(
        <ErrorBoundary {...defaultProps}>
          <ThrowError shouldThrow={true} errorMessage="Logger test" />
        </ErrorBoundary>
      );

      expect(mockErrorLogger.logError).toHaveBeenCalledWith(
        expect.objectContaining({ message: 'Logger test' }),
        expect.objectContaining({
          componentStack: expect.any(String),
          timestamp: expect.any(Number)
        })
      );
    });

    test('utilise le reporter d\'erreurs', () => {
      render(
        <ErrorBoundary {...defaultProps}>
          <ThrowError shouldThrow={true} errorMessage="Reporter test" />
        </ErrorBoundary>
      );

      expect(mockErrorReporter.reportError).toHaveBeenCalledWith({
        error: expect.objectContaining({ message: 'Reporter test' }),
        errorInfo: expect.objectContaining({ componentStack: expect.any(String) }),
        userAgent: expect.any(String),
        url: expect.any(String),
        timestamp: expect.any(Number)
      });
    });

    test('log les tentatives de récupération', () => {
      render(
        <ErrorBoundary {...defaultProps}>
          <ThrowError shouldThrow={true} errorMessage="Recovery log test" />
        </ErrorBoundary>
      );

      const retryButton = screen.getByRole('button', { name: /try again/i });
      fireEvent.click(retryButton);

      expect(mockErrorLogger.logUserAction).toHaveBeenCalledWith('error_boundary_retry', {
        retryAttempt: 1,
        maxRetries: 3,
        errorMessage: 'Recovery log test'
      });
    });

    test('log les récupérations réussies', () => {
      const { rerender } = render(
        <ErrorBoundary {...defaultProps}>
          <ThrowError shouldThrow={true} errorMessage="Success log test" />
        </ErrorBoundary>
      );

      const retryButton = screen.getByRole('button', { name: /try again/i });
      fireEvent.click(retryButton);

      rerender(
        <ErrorBoundary {...defaultProps}>
          <ThrowError shouldThrow={false} />
        </ErrorBoundary>
      );

      expect(mockErrorReporter.reportRecovery).toHaveBeenCalledWith({
        originalError: expect.objectContaining({ message: 'Success log test' }),
        recoveryAttempt: 1,
        timestamp: expect.any(Number)
      });
    });
  });

  describe('Gestion des erreurs avancée', () => {
    test('capture les erreurs de promesses non gérées', async () => {
      // Mock de l'événement unhandledrejection
      const unhandledRejectionEvent = new PromiseRejectionEvent('unhandledrejection', {
        promise: Promise.reject(new Error('Unhandled promise error')),
        reason: new Error('Unhandled promise error')
      });

      render(
        <ErrorBoundary {...defaultProps}>
          <div data-testid="promise-test">Promise test</div>
        </ErrorBoundary>
      );

      // Simuler l'erreur de promesse non gérée
      window.dispatchEvent(unhandledRejectionEvent);

      await waitFor(() => {
        expect(screen.getByTestId('error-boundary-fallback')).toBeInTheDocument();
        expect(screen.getByText(/unhandled promise error/i)).toBeInTheDocument();
      });
    });

    test('gère les erreurs avec des propriétés personnalisées', () => {
      const customError = new Error('Custom properties error');
      customError.code = 'CUSTOM_CODE';
      customError.severity = 'high';

      const ErrorWithCustomProps = () => {
        throw customError;
      };

      render(
        <ErrorBoundary {...defaultProps}>
          <ErrorWithCustomProps />
        </ErrorBoundary>
      );

      expect(mockErrorLogger.logError).toHaveBeenCalledWith(
        expect.objectContaining({
          message: 'Custom properties error',
          code: 'CUSTOM_CODE',
          severity: 'high'
        }),
        expect.any(Object)
      );
    });

    test('filtre les erreurs sensibles', () => {
      const sensitiveError = new Error('API key: sk-1234567890abcdef');

      const SensitiveErrorComponent = () => {
        throw sensitiveError;
      };

      render(
        <ErrorBoundary {...defaultProps} filterSensitiveInfo={true}>
          <SensitiveErrorComponent />
        </ErrorBoundary>
      );

      // L'erreur affichée devrait être filtrée
      expect(screen.queryByText(/sk-1234567890abcdef/)).not.toBeInTheDocument();
      expect(screen.getByText(/sensitive information removed/i)).toBeInTheDocument();
    });

    test('groupe les erreurs similaires', () => {
      const { rerender } = render(
        <ErrorBoundary {...defaultProps}>
          <ThrowError shouldThrow={true} errorMessage="Repeated error" />
        </ErrorBoundary>
      );

      // Simuler la même erreur plusieurs fois
      for (let i = 0; i < 5; i++) {
        rerender(
          <ErrorBoundary {...defaultProps}>
            <ThrowError shouldThrow={true} errorMessage="Repeated error" />
          </ErrorBoundary>
        );
      }

      expect(screen.getByText(/this error occurred 5 times/i)).toBeInTheDocument();
    });
  });

  describe('Performance et optimisation', () => {
    test('limite le nombre de logs pour éviter le spam', () => {
      // Déclencher de nombreuses erreurs rapidement
      for (let i = 0; i < 100; i++) {
        render(
          <ErrorBoundary {...defaultProps}>
            <ThrowError shouldThrow={true} errorMessage={`Spam error ${i}`} />
          </ErrorBoundary>
        );
      }

      // Le logger ne devrait pas être appelé plus de 10 fois (limite par défaut)
      expect(mockErrorLogger.logError.mock.calls.length).toBeLessThanOrEqual(10);
    });

    test('nettoie les anciens logs d\'erreurs', async () => {
      render(
        <ErrorBoundary {...defaultProps} maxErrorLogs={2}>
          <ThrowError shouldThrow={true} errorMessage="Cleanup test 1" />
        </ErrorBoundary>
      );

      // Attendre que les anciens logs soient nettoyés
      await waitFor(() => {
        expect(screen.queryByText(/old error logs cleaned/i)).toBeInTheDocument();
      });
    });

    test('utilise la mémorisation pour éviter les re-rendus inutiles', () => {
      const renderSpy = jest.fn();
      
      const SpyComponent = () => {
        renderSpy();
        return <div>Spy component</div>;
      };

      const { rerender } = render(
        <ErrorBoundary {...defaultProps}>
          <SpyComponent />
        </ErrorBoundary>
      );

      // Premier rendu
      expect(renderSpy).toHaveBeenCalledTimes(1);

      // Re-rendu avec les mêmes props
      rerender(
        <ErrorBoundary {...defaultProps}>
          <SpyComponent />
        </ErrorBoundary>
      );

      // Ne devrait pas re-rendre si pas d'erreur
      expect(renderSpy).toHaveBeenCalledTimes(1);
    });
  });

  describe('Accessibilité', () => {
    test('fournit des rôles ARIA appropriés', () => {
      render(
        <ErrorBoundary {...defaultProps}>
          <ThrowError shouldThrow={true} errorMessage="Accessibility test" />
        </ErrorBoundary>
      );

      const errorRegion = screen.getByRole('alert');
      expect(errorRegion).toBeInTheDocument();
      expect(errorRegion).toHaveAttribute('aria-live', 'assertive');
    });

    test('supporte la navigation au clavier', () => {
      render(
        <ErrorBoundary {...defaultProps}>
          <ThrowError shouldThrow={true} errorMessage="Keyboard test" />
        </ErrorBoundary>
      );

      const retryButton = screen.getByRole('button', { name: /try again/i });
      expect(retryButton).toHaveAttribute('tabIndex', '0');
      
      retryButton.focus();
      expect(document.activeElement).toBe(retryButton);
    });

    test('fournit des descriptions détaillées pour les lecteurs d\'écran', () => {
      render(
        <ErrorBoundary {...defaultProps}>
          <ThrowError shouldThrow={true} errorMessage="Screen reader test" />
        </ErrorBoundary>
      );

      const errorElement = screen.getByRole('alert');
      expect(errorElement).toHaveAttribute('aria-describedby');
      
      const description = document.getElementById(
        errorElement.getAttribute('aria-describedby')
      );
      expect(description).toHaveTextContent(/error occurred in the application/i);
    });

    test('annonce les changements d\'état aux lecteurs d\'écran', () => {
      const { rerender } = render(
        <ErrorBoundary {...defaultProps}>
          <ThrowError shouldThrow={true} errorMessage="State change test" />
        </ErrorBoundary>
      );

      const retryButton = screen.getByRole('button', { name: /try again/i });
      fireEvent.click(retryButton);

      expect(screen.getByRole('status')).toHaveTextContent(/retrying/i);

      rerender(
        <ErrorBoundary {...defaultProps}>
          <ThrowError shouldThrow={false} />
        </ErrorBoundary>
      );

      expect(screen.getByRole('status')).toHaveTextContent(/recovered/i);
    });
  });

  describe('Configuration et personnalisation', () => {
    test('supporte différents niveaux de verbosité', () => {
      render(
        <ErrorBoundary {...defaultProps} verbosity="minimal">
          <ThrowError shouldThrow={true} errorMessage="Minimal error" />
        </ErrorBoundary>
      );

      // Mode minimal devrait afficher moins d'informations
      expect(screen.queryByTestId('error-stack-trace')).not.toBeInTheDocument();
      expect(screen.queryByText(/component stack/i)).not.toBeInTheDocument();
    });

    test('permet de configurer les seuils d\'alerte', () => {
      render(
        <ErrorBoundary {...defaultProps} alertThreshold={1}>
          <ThrowError shouldThrow={true} errorMessage="Threshold test" />
        </ErrorBoundary>
      );

      // Devrait déclencher une alerte immédiatement
      expect(screen.getByRole('alert')).toHaveAttribute('aria-live', 'assertive');
    });

    test('supporte les hooks personnalisés d\'erreur', () => {
      const customHook = jest.fn();

      render(
        <ErrorBoundary {...defaultProps} onErrorHook={customHook}>
          <ThrowError shouldThrow={true} errorMessage="Hook test" />
        </ErrorBoundary>
      );

      expect(customHook).toHaveBeenCalledWith(
        expect.objectContaining({ message: 'Hook test' }),
        expect.any(Object)
      );
    });
  });
});

// Tests d'intégration
describe('ErrorBoundary - Tests d\'intégration', () => {
  test('fonctionne avec les composants JARVIS', () => {
    const JarvisComponent = () => {
      const [hasError, setHasError] = React.useState(false);
      
      if (hasError) {
        throw new Error('JARVIS component error');
      }
      
      return (
        <div>
          <h1>JARVIS Interface</h1>
          <button onClick={() => setHasError(true)}>Trigger Error</button>
        </div>
      );
    };

    render(
      <ErrorBoundary {...defaultProps}>
        <JarvisComponent />
      </ErrorBoundary>
    );

    const triggerButton = screen.getByText('Trigger Error');
    fireEvent.click(triggerButton);

    expect(screen.getByTestId('error-boundary-fallback')).toBeInTheDocument();
    expect(screen.getByText(/jarvis component error/i)).toBeInTheDocument();
  });

  test('cascade d\'erreurs avec plusieurs ErrorBoundary', () => {
    const Level1Error = () => {
      throw new Error('Level 1 error');
    };

    const Level2Component = () => (
      <ErrorBoundary {...defaultProps} fallback={() => <div>Level 2 fallback</div>}>
        <Level1Error />
      </ErrorBoundary>
    );

    render(
      <ErrorBoundary {...defaultProps} fallback={() => <div>Level 1 fallback</div>}>
        <Level2Component />
      </ErrorBoundary>
    );

    // L'erreur devrait être capturée au niveau 2
    expect(screen.getByText('Level 2 fallback')).toBeInTheDocument();
    expect(screen.queryByText('Level 1 fallback')).not.toBeInTheDocument();
  });

  test('récupération après erreur dans un workflow complexe', async () => {
    const ComplexWorkflow = ({ step }) => {
      if (step === 2) {
        throw new Error('Workflow step 2 failed');
      }
      
      return <div data-testid={`step-${step}`}>Step {step} completed</div>;
    };

    const { rerender } = render(
      <ErrorBoundary {...defaultProps}>
        <ComplexWorkflow step={1} />
      </ErrorBoundary>
    );

    expect(screen.getByTestId('step-1')).toBeInTheDocument();

    // Déclencher l'erreur à l'étape 2
    rerender(
      <ErrorBoundary {...defaultProps}>
        <ComplexWorkflow step={2} />
      </ErrorBoundary>
    );

    expect(screen.getByTestId('error-boundary-fallback')).toBeInTheDocument();

    // Retry
    const retryButton = screen.getByRole('button', { name: /try again/i });
    fireEvent.click(retryButton);

    // Passer à l'étape 3 (récupération)
    rerender(
      <ErrorBoundary {...defaultProps}>
        <ComplexWorkflow step={3} />
      </ErrorBoundary>
    );

    expect(screen.getByTestId('step-3')).toBeInTheDocument();
  });
});