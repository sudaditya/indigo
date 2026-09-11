import { NavLink } from 'react-router';

interface Tab {
  key: string;
  label: string;
  disabled?: boolean;
}

interface TabNavProps {
  workId: string;
  tabs: Tab[];
}

/**
 * Horizontal tab bar for the MD viewer.
 * NavLink applies `active` class automatically when its URL matches current route.
 */
export function TabNav({ workId, tabs }: TabNavProps) {
  return (
    <nav className="tab-nav">
      {tabs.map((tab) => {
        if (tab.disabled) {
          return (
            <span key={tab.key} className="tab-link tab-link-disabled">
              {tab.label}
              <span className="tab-badge">soon</span>
            </span>
          );
        }
        return (
          <NavLink
            key={tab.key}
            to={`/works/${workId}/${tab.key}`}
            className={({ isActive }) =>
              isActive ? 'tab-link tab-link-active' : 'tab-link'
            }
          >
            {tab.label}
          </NavLink>
        );
      })}
    </nav>
  );
}