%global _default_patch_fuzz 2
%{?filter_setup: %filter_from_requires /ant/d; %filter_setup}

Name:          scala
Version:       2.10.6
Release:       14
Summary:       Combination of object-oriented and functional programming
License:       BSD and CC0 and Public Domain
URL:           http://www.scala-lang.org/
Source0:       %{name}-%{version}.tar.gz
Source1:       scala-library-2.10.0-bnd.properties
Source2:       scala.gitinfo
Source3:       scala.keys
Source4:       scala.mime
Source5:       scala-mime-info.xml
Source6:       scala.ant.d
Source7:       scala-bootstript.xml
Patch0:        scala-2.10.0-tooltemplate.patch
Patch1:        scala-2.10.3-use_system_jline.patch
Patch2:        scala-2.10.3-compiler-pom.patch
Patch3:        scala-2.10.2-java7.patch
Patch4:        scala-2.10-jline.patch
Patch5:        scala-2.10.4-build_xml.patch
Patch6:	       scala-2.10.6-scaladoc-resources.patch
Patch6000:     CVE-2017-15288-pre.patch
Patch6001:     CVE-2017-15288.patch
BuildArch:     noarch

BuildRequires: java-devel >= 1:1.7.0, ant, ant-junit, ant-contrib, jline >= 2.10, aqute-bnd, junit, javapackages-local, scala
Requires:      jpackage-utils, jansi, java-headless >= 1:1.7.0, jline >= 2.10
Provides:      %{name}-apidoc%{?_isa} %{name}-apidoc
Obsoletes:     %{name}-apidoc
Provides:      %{name}-swing%{?_isa} %{name}-swing
Obsoletes:     %{name}-swing
Provides:      ant-scala%{?_isa} ant-scala
Obsoletes:     ant-scala

%description
Scala combines object-oriented and functional programming in one concise, high-level language.
Scala's static types help avoid bugs in complex applications, and its JVM and JavaScript runtimes
let you build high-performance systems with easy access to huge ecosystems of libraries.
It provides a common, uniform, and all-encompassing framework for collection types.
This framework enables you to work with data in memory at a high level, with the basic building
blocks of a program being whole collections, instead of individual elements.
This style of programming requires some learning. Fortunately, the adaptation is helped by several
nice properties of the Scala collections. They are easy to use, concise, safe, fast, universal.

%prep
%autosetup -p1

echo "starr.version=2.10.4\nstarr.use.released=0" > starr.number

cd src
rm -rf jline
cd -

sed -i '/is not supported by/d' build.xml
sed -i '/exec.*pull-binary-libs.sh/d' build.xml

pushd lib
  rm -rf scala-compiler.jar scala-library.jar scala-reflect.jar
  ln -s $(build-classpath scala/scala-compiler.jar) scala-compiler.jar
  ln -s $(build-classpath scala/scala-library.jar) scala-library.jar
  ln -s $(build-classpath scala/scala-reflect.jar) scala-reflect.jar
  pushd ant
    rm -rf ant.jar ant-contrib.jar
    ln -s $(build-classpath ant.jar) ant.jar
    ln -s $(build-classpath ant/ant-contrib) ant-contrib.jar
  popd
popd

cp -rf %{SOURCE7} .

sed -i -e 's!@JLINE@!%{_javadir}/jline/jline.jar!g' build.xml

echo echo $(head -n 1 %{SOURCE2}) > tools/get-scala-commit-sha
echo echo $(tail -n 1 %{SOURCE2}) > tools/get-scala-commit-date

chmod 755 tools/get-scala-*

%build
export ANT_OPTS="-Xms2048m -Xmx2048m %{nil}"

ant build || exit 1
cd build/pack/lib
mv scala-library.jar scala-library.jar.no
bnd wrap --properties %{SOURCE1} --output scala-library.jar --version "%{version}" scala-library.jar.no
cd -

%check
pushd test/files/run
  rm -rf parserJavaIdent.scala t6223.scala
  pushd ../presentation
    rm -rf implicit-member t5708 ide-bug-1000349 ide-bug-1000475 ide-bug-1000531 visibility ping-pong callcc-interpreter
    pushd ../../osgi/src
      rm -rf ReflectionToolboxTest.scala
    popd
  popd
popd

%install
install -d $RPM_BUILD_ROOT%{_bindir}
for prog in scaladoc fsc scala scalac scalap; do
        install -p -m 755 build/pack/bin/$prog $RPM_BUILD_ROOT%{_bindir}
done

install -p -m 755 -d $RPM_BUILD_ROOT%{_datadir}/scala/lib

%mvn_file ':{*}:jar:' %{name}/@1 %{_datadir}/scala/lib/@1
%mvn_file ':{*}:pom:' %{name}/@1 JPP.%{name}-@1

%mvn_package :scala-swing swing

for libname in scala-compiler scala-library scala-reflect scalap scala-swing ; do
        sed -i "s|@VERSION@|%{version}|" src/build/maven/$libname-pom.xml
        sed -i "s|@RELEASE_REPOSITORY@|http://nexus.scala-tools.org/content/repositories/releases|" src/build/maven/$libname-pom.xml
        sed -i "s|@SNAPSHOT_REPOSITORY@|http://nexus.scala-tools.org/content/repositories/snapshots|" src/build/maven/$libname-pom.xml
        %mvn_artifact src/build/maven/$libname-pom.xml build/pack/lib/$libname.jar
done
ln -s $(abs2rel %{_javadir}/jline/jline.jar %{_datadir}/scala/lib) $RPM_BUILD_ROOT%{_datadir}/scala/lib
ln -s $(abs2rel %{_javadir}/jansi/jansi.jar %{_datadir}/scala/lib) $RPM_BUILD_ROOT%{_datadir}/scala/lib

%mvn_install
install -d $RPM_BUILD_ROOT%{_sysconfdir}/ant.d
install -p -m 644 %{SOURCE6} $RPM_BUILD_ROOT%{_sysconfdir}/ant.d/scala

install -d $RPM_BUILD_ROOT%{_datadir}/mime-info
install -p -m 644 %{SOURCE3} %{SOURCE4} $RPM_BUILD_ROOT%{_datadir}/mime-info/

install -d $RPM_BUILD_ROOT%{_datadir}/mime/packages/
install -p -m 644 %{SOURCE5} $RPM_BUILD_ROOT%{_datadir}/mime/packages/

sed -i -e 's,@JAVADIR@,%{_javadir},g' -e 's,@DATADIR@,%{_datadir},g' $RPM_BUILD_ROOT%{_bindir}/*

%post
touch --no-create %{_datadir}/mime/packages > /dev/null 2>&1 || :

%postun
if [ $1 -eq 0 ]; then
update-mime-database %{_datadir}/mime > /dev/null 2>&1 || :
fi

%posttrans
update-mime-database -n %{_datadir}/mime > /dev/null 2>&1 || :

%files -f .mfiles
%license docs/LICENSE
%config %{_sysconfdir}/ant.d/*
%{_bindir}/*
%dir %{_datadir}/%{name}
%dir %{_datadir}/%{name}/lib
%{_datadir}/%{name}/lib/*.jar
%{_datadir}/mime-info/*
%{_datadir}/mime/packages/*
%{_javadir}/%{name}/*
/usr/share/maven*

%changelog
* Tue Feb 18 2020 Senlin Xia <xiasenlin1@huawei.com> - 2.10.6-14
- remove unused files
