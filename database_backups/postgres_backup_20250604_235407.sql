--
-- PostgreSQL database dump
--

-- Dumped from database version 17.5
-- Dumped by pg_dump version 17.5

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: public; Type: SCHEMA; Schema: -; Owner: postgres
--

-- *not* creating schema, since initdb creates it


ALTER SCHEMA public OWNER TO postgres;

--
-- Name: SCHEMA public; Type: COMMENT; Schema: -; Owner: postgres
--

COMMENT ON SCHEMA public IS '';


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: analyses; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.analyses (
    id integer NOT NULL,
    external_song_id integer,
    analysis_data text,
    version integer,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


ALTER TABLE public.analyses OWNER TO postgres;

--
-- Name: analyses_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.analyses_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.analyses_id_seq OWNER TO postgres;

--
-- Name: analyses_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.analyses_id_seq OWNED BY public.analyses.id;


--
-- Name: comments; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.comments (
    id integer NOT NULL,
    external_song_id integer,
    user_id integer,
    content text,
    upvote_count integer,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


ALTER TABLE public.comments OWNER TO postgres;

--
-- Name: comments_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.comments_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.comments_id_seq OWNER TO postgres;

--
-- Name: comments_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.comments_id_seq OWNED BY public.comments.id;


--
-- Name: external_song_references; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.external_song_references (
    id integer NOT NULL,
    external_id integer,
    title character varying,
    artist character varying,
    view_count integer,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


ALTER TABLE public.external_song_references OWNER TO postgres;

--
-- Name: external_song_references_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.external_song_references_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.external_song_references_id_seq OWNER TO postgres;

--
-- Name: external_song_references_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.external_song_references_id_seq OWNED BY public.external_song_references.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.users (
    id integer NOT NULL,
    username character varying,
    email character varying,
    hashed_password character varying,
    is_active boolean,
    created_at timestamp without time zone
);


ALTER TABLE public.users OWNER TO postgres;

--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.users_id_seq OWNER TO postgres;

--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- Name: analyses id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.analyses ALTER COLUMN id SET DEFAULT nextval('public.analyses_id_seq'::regclass);


--
-- Name: comments id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.comments ALTER COLUMN id SET DEFAULT nextval('public.comments_id_seq'::regclass);


--
-- Name: external_song_references id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.external_song_references ALTER COLUMN id SET DEFAULT nextval('public.external_song_references_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- Data for Name: analyses; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.analyses (id, external_song_id, analysis_data, version, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: comments; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.comments (id, external_song_id, user_id, content, upvote_count, created_at, updated_at) FROM stdin;
1	122476	1	good	13	2025-05-20 21:30:22.497948	2025-05-20 21:31:45.204691
2	122476	1	good	7	2025-05-20 21:39:11.42201	2025-05-20 21:40:03.479466
3	10024512	1	good	1	2025-05-20 21:51:38.104017	2025-05-20 21:51:45.61366
4	10024512	1	nice	1	2025-05-20 22:05:40.899947	2025-05-20 22:05:47.44929
6	205311	\N	Great song!	0	2025-05-20 22:16:05.12799	2025-05-20 22:16:05.128
7	205311	\N	Great song!	0	2025-05-20 22:16:48.082618	2025-05-20 22:16:48.082631
10	1063	\N	hey	0	2025-05-21 12:41:57.232632	2025-05-21 12:41:57.232641
11	2819932	\N	great	0	2025-06-04 18:00:03.387194	2025-06-04 18:00:03.387199
12	1063	\N	yes	0	2025-06-04 18:46:50.800813	2025-06-04 18:46:50.8011
\.


--
-- Data for Name: external_song_references; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.external_song_references (id, external_id, title, artist, view_count, created_at, updated_at) FROM stdin;
1	205311	Unknown	Unknown	0	2025-05-20 19:11:46.634848	2025-05-20 19:11:46.634857
2	10024512	Unknown	Unknown	0	2025-05-20 19:47:58.690299	2025-05-20 19:47:58.690305
3	122476	Unknown	Unknown	0	2025-05-20 20:39:42.023072	2025-05-20 20:39:42.023101
4	1063	Unknown	Unknown	0	2025-05-21 12:41:57.20213	2025-05-21 12:41:57.202137
5	2819932	Unknown	Unknown	0	2025-06-04 18:00:03.368154	2025-06-04 18:00:03.368159
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.users (id, username, email, hashed_password, is_active, created_at) FROM stdin;
1	maedah	\N	a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3	t	2025-05-20 21:30:16.648735
\.


--
-- Name: analyses_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.analyses_id_seq', 1, false);


--
-- Name: comments_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.comments_id_seq', 12, true);


--
-- Name: external_song_references_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.external_song_references_id_seq', 5, true);


--
-- Name: users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.users_id_seq', 1, true);


--
-- Name: analyses analyses_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.analyses
    ADD CONSTRAINT analyses_pkey PRIMARY KEY (id);


--
-- Name: comments comments_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.comments
    ADD CONSTRAINT comments_pkey PRIMARY KEY (id);


--
-- Name: external_song_references external_song_references_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.external_song_references
    ADD CONSTRAINT external_song_references_pkey PRIMARY KEY (id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: ix_analyses_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_analyses_id ON public.analyses USING btree (id);


--
-- Name: ix_comments_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_comments_id ON public.comments USING btree (id);


--
-- Name: ix_external_song_references_external_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX ix_external_song_references_external_id ON public.external_song_references USING btree (external_id);


--
-- Name: ix_external_song_references_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_external_song_references_id ON public.external_song_references USING btree (id);


--
-- Name: ix_users_email; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX ix_users_email ON public.users USING btree (email);


--
-- Name: ix_users_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_users_id ON public.users USING btree (id);


--
-- Name: ix_users_username; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX ix_users_username ON public.users USING btree (username);


--
-- Name: analyses analyses_external_song_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.analyses
    ADD CONSTRAINT analyses_external_song_id_fkey FOREIGN KEY (external_song_id) REFERENCES public.external_song_references(external_id);


--
-- Name: comments comments_external_song_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.comments
    ADD CONSTRAINT comments_external_song_id_fkey FOREIGN KEY (external_song_id) REFERENCES public.external_song_references(external_id);


--
-- Name: comments comments_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.comments
    ADD CONSTRAINT comments_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: SCHEMA public; Type: ACL; Schema: -; Owner: postgres
--

REVOKE USAGE ON SCHEMA public FROM PUBLIC;


--
-- PostgreSQL database dump complete
--

