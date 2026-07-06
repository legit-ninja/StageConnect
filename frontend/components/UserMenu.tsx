"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";

import { Avatar } from "@/components/Avatar";
import { ThemeToggle } from "@/components/ThemeToggle";
import { ApiError, User, fetchCurrentUser } from "@/lib/api";
import { clearToken, getToken } from "@/lib/auth";

import styles from "./UserMenu.module.css";

interface UserMenuProps {
  user?: User;
}

export function UserMenu({ user: userProp }: UserMenuProps) {
  const router = useRouter();
  const [fetchedUser, setFetchedUser] = useState<User | null | undefined>(() =>
    userProp !== undefined || getToken() ? undefined : null,
  );
  const [open, setOpen] = useState(false);
  const wrapperRef = useRef<HTMLDivElement>(null);
  const triggerRef = useRef<HTMLButtonElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (userProp !== undefined) return;
    const token = getToken();
    if (!token) return;
    fetchCurrentUser(token)
      .then(setFetchedUser)
      .catch((err: unknown) => {
        if (err instanceof ApiError && err.status === 401) {
          clearToken();
        }
        setFetchedUser(null);
      });
  }, [userProp]);

  const user = userProp !== undefined ? userProp : fetchedUser;

  useEffect(() => {
    if (!open) return;

    const firstFocusable = dropdownRef.current?.querySelector<HTMLElement>(
      "a, button, input",
    );
    firstFocusable?.focus();

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setOpen(false);
        triggerRef.current?.focus();
      }
    }

    function handlePointerDown(event: MouseEvent) {
      if (wrapperRef.current?.contains(event.target as Node)) return;
      setOpen(false);
    }

    document.addEventListener("keydown", handleKeyDown);
    document.addEventListener("mousedown", handlePointerDown);
    return () => {
      document.removeEventListener("keydown", handleKeyDown);
      document.removeEventListener("mousedown", handlePointerDown);
    };
  }, [open]);

  function closeMenu() {
    setOpen(false);
  }

  function handleSignOut() {
    clearToken();
    setOpen(false);
    router.push("/login");
  }

  if (user === undefined) {
    return <span className={styles.skeleton} aria-hidden="true" />;
  }

  if (!user) {
    return null;
  }

  const displayName = [user.first_name, user.last_name].filter(Boolean).join(" ").trim();
  const triggerLabel = displayName || user.email;
  const isVerified = user.verification_status === "verified";

  return (
    <div className={styles.wrapper} ref={wrapperRef}>
      <button
        ref={triggerRef}
        type="button"
        className={styles.trigger}
        aria-haspopup="true"
        aria-expanded={open}
        aria-controls="user-menu-dropdown"
        onClick={() => setOpen((prev) => !prev)}
      >
        <Avatar
          src={user.avatar_url}
          firstName={user.first_name ?? user.email}
          lastName={user.last_name}
          size="sm"
          verified={isVerified}
        />
        <span className={styles.triggerLabel}>{triggerLabel}</span>
      </button>

      {open ? (
        <div
          id="user-menu-dropdown"
          ref={dropdownRef}
          className={styles.dropdown}
          role="group"
          aria-label="Account menu"
        >
          <div className={styles.dropdownHeader}>
            <p className={styles.dropdownEmail}>{user.email}</p>
            <span className={styles.dropdownStatus}>
              {isVerified ? "Verified" : "Not verified"}
            </span>
          </div>

          <Link href="/settings" className={styles.item} onClick={closeMenu}>
            Settings
          </Link>
          <Link href="/dashboard" className={styles.item} onClick={closeMenu}>
            Dashboard
          </Link>

          {user.is_booker ? (
            <>
              <div className={styles.itemGroupLabel}>Booker</div>
              <Link href="/offerings" className={styles.item} onClick={closeMenu}>
                Find a gig
              </Link>
              <Link href="/booker/gigs" className={styles.item} onClick={closeMenu}>
                My gigs
              </Link>
            </>
          ) : null}

          {user.is_act_owner ? (
            <>
              <div className={styles.itemGroupLabel}>Act Owner</div>
              <Link href="/act-owner/offerings" className={styles.item} onClick={closeMenu}>
                Manage offerings
              </Link>
              <Link href="/act-owner/acts" className={styles.item} onClick={closeMenu}>
                My acts
              </Link>
              <Link href="/act-owner/gigs" className={styles.item} onClick={closeMenu}>
                Gig inbox
              </Link>
              <Link href="/act-owner/promoters" className={styles.item} onClick={closeMenu}>
                Promoter connections
              </Link>
            </>
          ) : null}

          {user.is_admin ? (
            <>
              <div className={styles.itemGroupLabel}>Admin</div>
              <Link href="/admin" className={styles.item} onClick={closeMenu}>
                Admin panel
              </Link>
            </>
          ) : null}

          <div className={styles.appearanceSection}>
            <div className={styles.itemGroupLabel}>Appearance</div>
            <ThemeToggle />
          </div>

          <button type="button" className={styles.signOut} onClick={handleSignOut}>
            Sign out
          </button>
        </div>
      ) : null}
    </div>
  );
}
